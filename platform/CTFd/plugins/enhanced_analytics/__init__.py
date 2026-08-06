from flask import request
from CTFd.models import Tracking, db, ChallengeFiles
from CTFd.utils.user import get_ip, get_current_user
from CTFd.plugins import register_plugin_assets_directory
from CTFd.utils.plugins import register_script

def load(app):
    register_plugin_assets_directory(app, base_path='/plugins/enhanced_analytics/assets/')
    register_script('/plugins/enhanced_analytics/assets/script.js')

    @app.before_request
    def track_analytics():
        user = get_current_user()
        if not user: return
        
        # Track Downloads
        if request.path.startswith('/files/') and request.method == 'GET':
            parts = request.path.split('/')
            if len(parts) >= 3:
                loc = '/'.join(parts[2:]).split('?')[0]
                cf = ChallengeFiles.query.filter_by(location=loc).first()
                if cf and not Tracking.query.filter_by(user_id=user.id, type='challenges.download', target=cf.challenge_id).first():
                    db.session.add(Tracking(user_id=user.id, ip=get_ip(), type='challenges.download', target=cf.challenge_id))
                    db.session.commit()
        
        # Track Anti-Cheat
        if request.path.endswith('/api/v1/challenges/attempt') and request.method == 'POST':
            try:
                data = request.get_json()
                diff = data.get('paste_diff')
                if diff is not None and 0 <= diff < 10:
                    db.session.add(Tracking(user_id=user.id, ip=get_ip(), type='anti_cheat.alert', target=data.get('challenge_id')))
                    db.session.commit()
            except: pass
