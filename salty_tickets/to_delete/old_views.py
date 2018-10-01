from flask import render_template, jsonify, Response
from salty_tickets import app
from salty_tickets.forms import VoteForm, VoteAdminForm
from salty_tickets.to_delete.database import db_session
from salty_tickets.to_delete.sql_models import Vote, VotingSession


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()



VOTER_UUID_COOKIE_NAME = 'voter'


@app.route('/vote')
def vote():
    form = VoteForm()
    return render_template('voting/vote.html', form=form)


@app.route('/vote/submit', methods=['POST'])
def vote_submit():
    form = VoteForm()
    if form.validate_on_submit():
        voter_uuid = form.client_fingerprint.data
        vote = Vote(voter_id=voter_uuid, vote=form.options.data)
        db_session.add(vote)
        db_session.commit()
        return 'Success'
    else:
        return jsonify(form.errors)


@app.route('/vote/admin', methods=['GET', 'POST'])
def vote_admin():
    form = VoteAdminForm()
    voting_session = VotingSession.query.order_by(VotingSession.id.desc()).first()
    if form.validate_on_submit():

        if form.start_voting.data:
            voting_session = VotingSession(name=form.name.data)
            db_session.add(voting_session)
            db_session.commit()

        elif form.stop_voting.data:
            voting_session.stop()
            db_session.commit()

    if voting_session:
        form.name.data = voting_session.name

        if voting_session.end_timestamp:
            form.stop_voting.data = True

        votes_query = Vote.query.filter(Vote.vote_timestamp > voting_session.start_timestamp)
        if voting_session.end_timestamp:
            votes_query = votes_query.filter(Vote.vote_timestamp < voting_session.end_timestamp)
        all_votes = votes_query.all()
        all_votes_dict = {v.voter_id:v.vote for v in all_votes}

        res_left = len([k for k,v in all_votes_dict.items() if v=='left'])
        res_right = len([k for k,v in all_votes_dict.items() if v=='right'])
        results_data = {
            'left': res_left,
            'right': res_right
        }
        progess_max = max(20, max(res_left,res_right))
        progress_data = {
            'total_max': progess_max,
            'left_pcnt': int(res_left*100/progess_max),
            'right_pcnt': int(res_right*100/progess_max),
        }
    else:
        results_data = None
    return render_template('voting/admin.html', form=form, results_data=results_data, progress_data=progress_data)


@app.route('/vote/admin/data.csv')
def vote_data():
    import pandas as pd
    from salty_tickets.to_delete.database import engine
    voting_sessions_df = pd.read_sql_query(VotingSession.query.statement, engine)
    votes_df = pd.read_sql_query(Vote.query.statement, engine)

    start_date = pd.datetime.today().date() - pd.DateOffset(days=2)
    voting_sessions_df = voting_sessions_df[voting_sessions_df.end_timestamp > start_date]
    votes_start = voting_sessions_df.start_timestamp.iloc[0]
    votes_df = votes_df[votes_df.vote_timestamp >= votes_start]

    votes_df['session_id'] = None
    for ix, voting_session in voting_sessions_df.iterrows():
        votes_mask = votes_df.vote_timestamp.between(voting_session.start_timestamp, voting_session.end_timestamp)
        votes_df.session_id[votes_mask] = voting_session.id

    voting_sessions_df.index = voting_sessions_df.id
    voting_sessions_df.drop('id', axis=1, inplace=True)
    votes_df = votes_df.join(voting_sessions_df, on='session_id', how='inner')

    vote_options = votes_df.vote.unique()
    for vote_option in vote_options:
        votes_df[vote_option] = None

    for ix, vote in votes_df.iterrows():
        query_votes = votes_df[votes_df.vote_timestamp.between(vote.start_timestamp, vote.vote_timestamp)]
        grouped = query_votes.groupby('voter_id').last()

        for vote_option in vote_options:
            votes_df.loc[ix, vote_option] = grouped.vote[grouped.vote == vote_option].count()

    data_csv = votes_df.to_csv(index=False)
    return Response(
        data_csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=data.csv"})

