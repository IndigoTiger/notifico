# -*- coding: utf8 -*-
import urllib
import requests

from flask import (
    Blueprint,
    render_template,
    g,
    url_for,
    redirect,
    request
)
from flask.ext import wtf
from github import Github

from frontend import user_required, app
from frontend.models import AuthToken, Project

pimport = Blueprint('pimport', __name__, template_folder='templates')


class GithubForm(wtf.Form):
    projects = wtf.BooleanField('Import Projects', default=True, description=(
        'Imports all of your public and private repositories. Private repos'
        ' will be imported as private and will never store messages.'
    ))
    set_hooks = wtf.BooleanField('Set Hooks', default=True, description=(
        'Sets up each project on your account with event hooks.'
    ))


@pimport.route('/github', methods=['GET', 'POST'])
@user_required
def github():
    """
    Import/merge the users existing Github projects, optionally setting up
    web hooks for them.
    """
    if 'code' in request.args:
        # We've finished step one and have a temporary token.
        r = requests.post('https://github.com/login/oauth/access_token',
            params={
                'client_id': app.config['SERVICE_GITHUB_CLIENT_ID'],
                'client_secret': app.config['SERVICE_GITHUB_CLIENT_SECRET'],
                'code': request.args['code']
        }, headers={
            'Accept': 'application/json'
        })
        result = r.json
        token = AuthToken.new(result['access_token'], 'github')
        g.db.session.add(token)
        g.user.tokens.append(token)
        g.db.session.commit()
        return redirect(url_for('.github'))

    # Check to make sure the user has previously authenticated.
    access_token = AuthToken.query.filter_by(
        name='github',
        owner_id=g.user.id
    ).first()

    if access_token is None:
        # The user hasn't setup Github yet, we need to get their OAuth
        # token.
        return redirect(
            'https://github.com/login/oauth/authorize?{0}'.format(
                urllib.urlencode({
                    'client_id': app.config['SERVICE_GITHUB_CLIENT_ID'],
                    'scope': 'repo'
                })
            )
        )

    summary = None
    form = GithubForm()
    if form.validate_on_submit():
        summary = []
        # WTForms "forgets" disabled fields. This should /always/ be True.
        form.projects.data = True

        git = Github(access_token.token)
        for repo in git.get_user().get_repos():
            p = Project.by_name(repo.name)
            if p is not None:
                summary.append((
                    (
                        'Skipping {0} as a project with that name already'
                        ' exists.'
                    ).format(repo.name),
                    False
                ))
                continue

            p = Project.new(
                repo.name,
                public=not repo.private,
                website=repo.homepage
            )
            p.full_name = '{0}/{1}'.format(g.user.username, p.name)
            g.user.projects.append(p)
            g.db.session.add(p)
            summary.append((
                'Project {0} created.'.format(repo.name),
                True
            ))
        g.db.session.commit()

    return render_template('github.html',
        form=form,
        summary=summary
    )