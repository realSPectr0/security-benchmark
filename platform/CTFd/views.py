import os  # noqa: I001

from flask import Blueprint, abort
from flask import current_app as app
from flask import (
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from jinja2.exceptions import TemplateNotFound
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import safe_join

from CTFd.cache import cache
from CTFd.constants.config import (
    AccountVisibilityTypes,
    ChallengeVisibilityTypes,
    ConfigTypes,
    RegistrationVisibilityTypes,
    ScoreVisibilityTypes,
)
from CTFd.constants.themes import DEFAULT_THEME
from CTFd.models import (
    Admins,
    Files,
    Notifications,
    Pages,
    Solutions,
    Teams,
    Users,
    UserTokens,
    db,
)
from CTFd.utils import config, get_config, set_config
from CTFd.utils import user as current_user
from CTFd.utils import validators
from CTFd.utils.config import can_send_mail, is_setup, is_teams_mode
from CTFd.utils.config.pages import build_markdown, get_page
from CTFd.utils.config.visibility import challenges_visible
from CTFd.utils.dates import ctf_ended, ctftime, view_after_ctf
from CTFd.utils.decorators import authed_only
from CTFd.utils.health import check_config, check_database
from CTFd.utils.helpers import get_errors, get_infos, markup
from CTFd.utils.modes import USERS_MODE
from CTFd.utils.security.auth import login_user
from CTFd.utils.security.csrf import generate_nonce
from CTFd.utils.security.signing import (
    BadSignature,
    BadTimeSignature,
    SignatureExpired,
    serialize,
    unserialize,
)
from CTFd.utils.uploads import get_uploader, upload_file
from CTFd.utils.user import authed, get_current_team, get_current_user, get_ip, is_admin

views = Blueprint("views", __name__)


@views.route("/setup", methods=["GET", "POST"])
def setup():
    return redirect(url_for("views.static_html"))


@views.route("/notifications", methods=["GET"])
def notifications():
    notifications = Notifications.query.order_by(Notifications.id.desc()).all()
    return render_template("notifications.html", notifications=notifications)


@views.route("/settings", methods=["GET"])
@authed_only
def settings():
    infos = get_infos()
    errors = get_errors()

    user = get_current_user()

    if is_teams_mode() and get_current_team() is None:
        team_url = url_for("teams.private")
        infos.append(
            markup(
                f'In order to participate you must either <a href="{team_url}">join or create a team</a>.'
            )
        )

    tokens = UserTokens.query.filter_by(user_id=user.id).all()

    prevent_name_change = get_config("prevent_name_change")

    if can_send_mail() and not user.verified:
        confirm_url = markup(url_for("auth.confirm", flow="init"))
        infos.append(
            markup(
                "Your email address isn't confirmed!<br>"
                f'To confirm your email address please <a href="{confirm_url}">click here</a>.'
            )
        )

    return render_template(
        "settings.html",
        name=user.name,
        email=user.email,
        language=user.language,
        website=user.website,
        affiliation=user.affiliation,
        country=user.country,
        tokens=tokens,
        prevent_name_change=prevent_name_change,
        infos=infos,
        errors=errors,
    )


@views.route("/", defaults={"route": "index"})
@views.route("/<path:route>")
def static_html(route):
    """
    Route in charge of routing users to Pages.
    :param route:
    :return:
    """
    page = get_page(route)
    if page is None:
        abort(404)
    else:
        if page.auth_required and authed() is False:
            return redirect(url_for("auth.login", next=request.full_path))

        return render_template("page.html", content=page.html, title=page.title)


@views.route("/tos")
def tos():
    tos_url = get_config("tos_url")
    tos_text = get_config("tos_text")
    if tos_url:
        return redirect(tos_url)
    elif tos_text:
        return render_template("page.html", content=build_markdown(tos_text))
    else:
        abort(404)


@views.route("/privacy")
def privacy():
    privacy_url = get_config("privacy_url")
    privacy_text = get_config("privacy_text")
    if privacy_url:
        return redirect(privacy_url)
    elif privacy_text:
        return render_template("page.html", content=build_markdown(privacy_text))
    else:
        abort(404)


@views.route("/files", defaults={"path": ""})
@views.route("/files/<path:path>")
def files(path):
    """
    Route in charge of dealing with making sure that CTF challenges are only accessible during the competition.
    :param path:
    :return:
    """
    f = Files.query.filter_by(location=path).first_or_404()
    if f.type == "challenge":
        if challenges_visible():
            if current_user.is_admin() is False:
                if not ctftime():
                    if ctf_ended() and view_after_ctf():
                        pass
                    else:
                        abort(403)
        else:
            # User cannot view challenges based on challenge visibility
            # e.g. ctf requires registration but user isn't authed or
            # ctf requires admin account but user isn't admin

            # Allow downloads if a valid token is provided
            # For example with wget downloads
            token = request.args.get("token", "")
            try:
                data = unserialize(token, max_age=3600)
            # The token isn't expired or broken
            except (BadTimeSignature, SignatureExpired, BadSignature):
                abort(403)

            # Determine the user and team asking to download
            user_id = data.get("user_id")
            team_id = data.get("team_id")
            file_id = data.get("file_id")
            user = Users.query.filter_by(id=user_id).first()
            team = Teams.query.filter_by(id=team_id).first()

            if not ctftime():
                # It's not CTF time. The only edge case is if the CTF is ended
                # but we have view_after_ctf enabled
                if ctf_ended() and view_after_ctf():
                    pass
                else:
                    if user.type == "admin":
                        # We allow admins to download files by URL before CTF start
                        pass
                    else:
                        # In all other situations we should block challenge files
                        abort(403)

            # Check user is admin if challenge_visibility is admins only
            if (
                get_config(ConfigTypes.CHALLENGE_VISIBILITY) == "admins"
                and user.type != "admin"
            ):
                abort(403)

            # Check that the user exists and isn't banned
            if user:
                if user.banned:
                    abort(403)
            else:
                abort(403)

            # Check that the team isn't banned
            if team:
                if team.banned:
                    abort(403)
            else:
                pass

            # Check that the token properly refers to the file
            if file_id != f.id:
                abort(403)

    elif f.type == "solution":
        s = Solutions.query.filter_by(id=f.solution_id).first_or_404()
        if s.state != "visible" or s.challenge.state != "visible":
            # Admins can see solution files for preview purposes
            if current_user.is_admin() is True:
                pass
            else:
                abort(404)

    uploader = get_uploader()
    try:
        return uploader.download(f.location)
    except IOError:
        abort(404)


@views.route("/themes/<theme>/static/<path:path>")
def themes(theme, path):
    """
    General static file handler
    :param theme:
    :param path:
    :return:
    """
    for cand_path in (
        safe_join(app.root_path, "themes", cand_theme, "static", path)
        # The `theme` value passed in may not be the configured one, e.g. for
        # admin pages, so we check that first
        for cand_theme in (theme, *config.ctf_theme_candidates())
    ):
        # Handle werkzeug behavior of returning None on malicious paths
        if cand_path is None:
            abort(404)
        if os.path.isfile(cand_path):
            return send_file(cand_path, max_age=3600)
    abort(404)


@views.route("/themes/<theme>/static/<path:path>")
def themes_beta(theme, path):
    """
    This is a copy of the above themes route used to avoid
    the current appending of .dev and .min for theme assets.

    In CTFd 4.0 this url_for behavior and this themes_beta
    route will be removed.
    """
    for cand_path in (
        safe_join(app.root_path, "themes", cand_theme, "static", path)
        # The `theme` value passed in may not be the configured one, e.g. for
        # admin pages, so we check that first
        for cand_theme in (theme, *config.ctf_theme_candidates())
    ):
        # Handle werkzeug behavior of returning None on malicious paths
        if cand_path is None:
            abort(404)
        if os.path.isfile(cand_path):
            return send_file(cand_path, max_age=3600)
    abort(404)


@views.route("/healthcheck")
def healthcheck():
    if check_database() is False:
        return "ERR", 500
    if check_config() is False:
        return "ERR", 500
    return "OK", 200


@views.route("/debug")
def debug():
    if app.config.get("SAFE_MODE") is True:
        ip = get_ip()
        headers = dict(request.headers)
        # Remove Cookie item
        headers.pop("Cookie", None)
        resp = ""
        resp += f"IP: {ip}\n"
        for k, v in headers.items():
            resp += f"{k}: {v}\n"
        r = make_response(resp)
        r.mimetype = "text/plain"
        return r
    abort(404)


@views.route("/robots.txt")
def robots():
    text = get_config("robots_txt", "User-agent: *\nDisallow: /admin\n")
    r = make_response(text, 200)
    r.mimetype = "text/plain"
    return r
