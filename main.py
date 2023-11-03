from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

messages = []
filtered_messages = []
max_messages = 10
previous_search = None

def get_next_id():
    return len(messages)

def create_app():
    app = Flask(__name__)
    

    @app.route('/policies')
    def politics():
        return render_template('policies.html')

    @app.route('/', methods=['GET', 'POST'])
    def index():
        
        error_message = ""

        
        filter_tag = request.args.get('filter')
        if filter_tag is None:
            filter_tag = 'all'

        global previous_search
        if request.method == 'POST':
            name = request.form.get('name', "")
            post = request.form.get('post', "")
            categories = request.form.getlist('categories')
            comment = request.form.get('comment', "")
            parent_id = request.form.get('parent_id', "")
            filter_tag = request.form.get('filter')
            if filter_tag is None:
                filter_tag = 'all'
            
            if not post.strip() and (comment is None or not comment.strip()):
                return render_template('index.html', messages=messages[-max_messages:], error="Message or comment cannot be blank.", categories=["Secrets", "Family", "Health", "Confession", "Other"], filter=filter_tag)

            if len(categories) > 2:
                return render_template('index.html', messages=messages[-max_messages:], categories=["Secrets", "Family", "Health", "Confession", "Other"], error="You can select up to 2 categories.", filter=filter_tag)

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if comment:
                comment_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                comment_data = {
                    'comment': comment,
                    'timestamp': comment_timestamp,
                    'filter': filter_tag,
                    'categories': categories
                }
                
                if parent_id:
                    parent_id = int(parent_id)
                    if parent_id >= 0 and parent_id < len(messages):
                        messages[parent_id]['comments'].append(comment_data)

                if previous_search is None:
                    return redirect(url_for('index', filter=filter_tag))
                else:
                    return redirect(url_for('index', filter=filter_tag, search=previous_search))
                
            else:
                message = {
                    'id': get_next_id(),
                    'name': name,
                    'post': post,
                    'timestamp': timestamp,
                    'categories': categories,
                    'comments': []
                }
                messages.append(message)

        filtered_messages = [message for message in messages if filter_tag is None or filter_tag == 'all' or filter_tag in message['categories']]

        search_query = request.args.get('search')
        error_message = ""
        if request.method == 'GET':
            if search_query is not None and search_query.strip():
                filtered_messages = [message for message in filtered_messages if search_query.lower() in message['post'].lower()]
                previous_search = search_query
                if not filtered_messages:
                    error_message = "No results found"
            elif search_query is not None and len(search_query) == 0:
                filtered_messages = []
                error_message = "No results found"
            elif search_query is None or len(search_query) == 0:
                previous_search = None
            
        return render_template('index.html', messages=filtered_messages[-max_messages:], error=error_message, categories=["Secrets", "Family", "Health", "Confession", "Other"], filter=filter_tag, search=search_query)

    return app
if __name__ == '__main__':
    app = create_app()
    app.run()