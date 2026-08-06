import os,json
from CTFd.models import Challenges,Flags,db
def load(app):
    with app.app_context():
        b=os.path.join(os.path.dirname(app.root_path),'challenges')
        if not os.path.exists(b):os.makedirs(b)
        for d in os.listdir(b):
            p=os.path.join(b,d,'challenge.json')
            if os.path.exists(p):
                with open(p) as f:c=json.load(f)
                if not Challenges.query.filter_by(name=c['name']).first():
                    ch=Challenges(name=c['name'],category=c['category'],description=c['description'],value=c.get('value',100),state='visible',type='standard')
                    db.session.add(ch);db.session.commit()
                    for fl in c.get('flags',[]):db.session.add(Flags(challenge_id=ch.id,content=fl,type='static'))
                    db.session.commit()
