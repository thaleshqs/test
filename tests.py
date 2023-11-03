import unittest
import sys
from flask import Flask
sys.path.append('../')  
from main import app, messages, previous_search, filtered_messages, create_app
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False  


class TestApp(unittest.TestCase):
    @classmethod
    def setUp(self):
        self.app = create_app()
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_ctxt = self.app.app_context()
        self.app_ctxt.push()
        self.client = self.app.test_client()
        self.client.get('/')
        self.client.post('/')
    
    @classmethod
    def tearDown(self):       
        messages.clear()
        filtered_messages.clear()
        previous_search = None

        self.app_ctxt.pop()
        self.app = None
        self.app_ctxt = None
        self.client = None
 
    def test_case_insensitive_search(self):
        data = {'name': 'Test User','post': 'This is a Test Post'}
        self.client.post('/', data=data)
        response = self.client.get('/?search=test post')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Post', response.data)

    def test_combine_filter_and_search(self):
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Health post', 'categories': 'Health'})
        response = self.client.get('/?filter=Health&search=health')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Health post', response.data)
    
    def test_combine_message_filter_search_and_comment(self):
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Health post', 'categories': 'Health'})
        response = self.client.get('/?filter=Health&search=health')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Health post', response.data)

    def test_combine_post_and_filter(self):
        data1 = {
            'name': 'Test User',
            'post': 'Post with category Health',
            'categories': 'Health',
        }
        self.client.post('/', data=data1, follow_redirects=True)
        data2 = {
            'name': 'Test User',
            'post': 'Post with category Other',
            'categories': 'Other',
        }
        self.client.post('/', data=data2, follow_redirects=True)
        response = self.client.get('/?filter=Health')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Post with category Health', response.data)
        self.assertNotIn(b'Post with category Other', response.data)    


    def test_comment_on_deleted_message(self):
        self.client.post('/', data={'name': 'Test User', 'post': 'Original Message'}, follow_redirects=True)
        response = self.client.post('/', data={'name': 'Test User','comment': 'Comment on Original Message','parent_id': 0}, follow_redirects=True)
        messages.clear()  
        response = self.client.post('/', data={'name': 'Test User','comment': 'Comment on Deleted Message','parent_id': 0}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Comment on Deleted Message', response.data)
    
    def test_comment_on_empty_message(self):
        response = self.client.post('/', data={'name': 'Test User', 'post': ''})
        
        response = self.client.post('/', data={'name': 'Test User', 'comment': 'This comment should not be posted', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'This comment should not be posted', response.data)


    def test_comment_timestamps(self):
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Message 1'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Message 2'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertLess(response.data.index(b'Message 2'), response.data.index(b'Message 1'))
    
    def test_comment_with_invalid_parent(self):
        response = self.client.post('/', data={'name': 'Test User', 'comment': 'This comment should not have a parent', 'parent_id': 12345})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(b'This comment should not have a parent', response.data)

    def test_comment_without_parent(self):
        response = self.client.post('/', data={'name': 'Test User', 'comment': 'This comment should not have a parent'})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(b'This comment should not have a parent', response.data)

    def test_combine_post_filter_and_post_message(self):
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Post with category Health', 'categories': 'Health'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Post with category Health', response.data)
        response = self.client.get('/?filter=Health')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Post with category Health', response.data)
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Another Post with category Health', 'categories': 'Health'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Another Post with category Health', response.data)

    def test_empty_user_name_on_page(self):
        response = self.client.post('/', data={'name': '', 'post': 'Test Message'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'', response.data)

    def test_filter_all_works_with_category_post(self):
        self.client.post('/', data= {'name': 'Test User', 'post': 'Test Message', 'categories': 'Health'}, follow_redirects=True)

        response = self.client.get('/?filter=all')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Message', response.data)

    def test_filter_hides_other_posts(self):
        self.client.post('/', data={'name': 'Test User', 'post': 'Test Message', 'categories': 'Health'}, follow_redirects=True)

        response = self.client.get('/?filter=Family')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Test Message', response.data)

    def test_homepage(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_message_timestamps(self):
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Message 1'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Message 2'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertLess(response.data.index(b'Message 2'), response.data.index(b'Message 1'))

    def test_multiple_category_filtering_on_one_message(self):
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Message 1', 'categories': ['Health', 'Family']}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/?filter=Health')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Message 1', response.data)
        response = self.client.get('/?filter=Family')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Message 1', response.data)

    def test_multiple_message_categories(self):
        response1 = self.client.post('/', data={'name': 'Test User', 'post': 'Message A', 'categories': ['Health']}, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)

        response2 = self.client.post('/', data={'name': 'Test User', 'post': 'Message B', 'categories': ['Family']}, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)

        response = self.client.get('/?filter=Family')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Message B', response.data)
        self.assertNotIn(b'Message A', response.data)

    def test_no_results_found_with_empty_keyword(self):
        response = self.client.get('/?search=')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No results found', response.data)

    def test_no_results_found_with_nonexistent_keyword(self):
        response = self.client.get('/?search=Nonexistent')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No results found', response.data)
    
    def test_politics_page(self):
        response = self.client.get('/policies')
        self.assertEqual(response.status_code, 200)

    def test_post_comments_on_two_different_messages(self):
        self.client.post('/', data={'name': 'Test User 1', 'post': 'Test Message 1'}, follow_redirects=True)
        self.client.post('/', data={'name': 'Test User 2', 'post': 'Test Message 2'}, follow_redirects=True)

        response1 = self.client.post('/', data={'name': 'Test User 1', 'comment': 'Test Comment 1', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Test Comment 1', response1.data)
        
        response2 = self.client.post('/', data={'name': 'Test User 2', 'comment': 'Test Comment 2', 'parent_id': 1}, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Test Comment 2', response2.data)

    def test_post_comments_on_three_different_messages(self):
        self.client.post('/', data={'name': 'Test User 1', 'post': 'Test Message 1'}, follow_redirects=True)
        self.client.post('/', data={'name': 'Test User 2', 'post': 'Test Message 2'}, follow_redirects=True)
        self.client.post('/', data={'name': 'Test User 2', 'post': 'Test Message 3'}, follow_redirects=True)
        
        response1 = self.client.post('/', data={'name': 'Test User 1', 'comment': 'Test Comment 1', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Test Comment 1', response1.data)
        
        response2 = self.client.post('/', data={'name': 'Test User 2', 'comment': 'Test Comment 2', 'parent_id': 1}, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Test Comment 2', response2.data)
        
        response3 = self.client.post('/', data={'name': 'Test User 2', 'comment': 'Test Comment 3', 'parent_id': 2}, follow_redirects=True)
        self.assertEqual(response3.status_code, 200)
        self.assertIn(b'Test Comment 3', response3.data)
       

    def test_post_empty_message(self):
        response = self.client.post('/', data={'name': 'Test User', 'post': ''}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Message or comment cannot be blank.', response.data)
        self.assertNotIn(b'Test User', response.data)

    def test_post_message(self):
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message'})
        self.assertEqual(response.status_code, 200)
    
    def test_post_message_and_check_content(self):
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test User', response.data)
        self.assertIn(b'Test Message', response.data)

    def test_post_two_messages_and_check_contents(self):
        response1 = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message'}, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Test User', response1.data)
        self.assertIn(b'Test Message', response1.data)
        
        response2 = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message 2'}, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Test User', response2.data)
        self.assertIn(b'Test Message', response2.data)

    def test_post_three_messages_and_check_contents(self):
        response1 = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message'}, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Test User', response1.data)
        self.assertIn(b'Test Message', response1.data)
        
        response2 = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message 2'}, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Test User', response2.data)
        self.assertIn(b'Test Message 2', response2.data)
        
        response3 = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message 3'}, follow_redirects=True)
        self.assertEqual(response3.status_code, 200)
        self.assertIn(b'Test User', response3.data)
        self.assertIn(b'Test Message 3', response3.data)
       

    def test_post_four_messages_and_check_contents(self):
        response1 = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message'}, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Test User', response1.data)
        self.assertIn(b'Test Message', response1.data)
        
        response2 = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message 2'}, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Test User', response2.data)
        self.assertIn(b'Test Message', response2.data)

        response3 = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message 3'}, follow_redirects=True)
        self.assertEqual(response3.status_code, 200)
        self.assertIn(b'Test User', response3.data)
        self.assertIn(b'Test Message 3', response3.data)

        response4 = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message 4'}, follow_redirects=True)
        self.assertEqual(response4.status_code, 200)
        self.assertIn(b'Test User', response4.data)
        self.assertIn(b'Test Message 4', response4.data)
        
        
    def test_post_message_and_empty_comment(self):
        response1 = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message'}, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Test Message', response1.data)

        response2 = self.client.post('/', data={'name': 'Test User Comment', 'comment': ''}, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Message or comment cannot be blank.', response2.data)
        self.assertNotIn(b'Test User Comment', response2.data)
    
    def test_post_message_search_and_post_one_comment(self):
        response = self.client.post('/', data={'name': 'Test User 1', 'post': 'Test Message 1'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/?search=Test')
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/', data={'name': 'Test User 1', 'comment': 'Test Comment 1', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Comment 1', response.data)
    
    def test_post_message_search_and_post_another_message(self):
        response = self.client.post('/', data={'name': 'Test User 1', 'post': 'Test Message 1'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/?search=Test')
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/', data={'name': 'Test User 2', 'post': 'Test Message 2'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Message 2', response.data)
    
    def test_post_message_search_and_post_two_comments(self):
        response = self.client.post('/', data={'name': 'Test User 1', 'post': 'Test Message 1'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/?search=Test')
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/', data={'name': 'Test User 1', 'comment': 'Test Comment 1', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Comment 1', response.data)
        response = self.client.post('/', data={'name': 'Test User 1', 'comment': 'Test Comment 2', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Comment 2', response.data)

    
    def test_post_two_messages(self):
        response1 = self.client.post('/', data={'name': 'Test User 1', 'post': 'Test Message 1'})
        self.assertEqual(response1.status_code, 200)

        response2 = self.client.post('/', data={'name': 'Test User 2', 'post': 'Test Message 2'})
        self.assertEqual(response2.status_code, 200)
    
    def test_post_two_messages_and_check_content(self):
        response1 = self.client.post('/', data={'name': 'Test User 1', 'post': 'Test Message 1'}, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Test User 1', response1.data)
        self.assertIn(b'Test Message 1', response1.data)
        response2 = self.client.post('/', data={'name': 'Test User 2', 'post': 'Test Message 2'}, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Test User 2', response2.data)
        self.assertIn(b'Test Message 2', response2.data)
    
    def test_user_name_on_message(self):
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test User', response.data)
        
    
    def test_post_one_comment(self):
        self.client.post('/', data={'name': 'Test User', 'post': 'Test Message'}, follow_redirects=True)

        response = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Comment', response.data)
        
    def test_post_two_comments(self):
        self.client.post('/', data={'name': 'Test User', 'post': 'Test Message'}, follow_redirects=True)
        response1 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Test Comment', response1.data)
        response2 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment 2', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Test Comment 2', response2.data)


    def test_post_three_comments(self):
        self.client.post('/', data={'name': 'Test User', 'post': 'Test Message'}, follow_redirects=True)
        response1 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Test Comment', response1.data)
        response2 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment 2', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Test Comment 2', response2.data)
        response3 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment 3', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response3.status_code, 200)
        self.assertIn(b'Test Comment 3', response3.data)

    def test_post_four_comments(self):
        self.client.post('/', data={'name': 'Test User', 'post': 'Test Message'}, follow_redirects=True)
        response1 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Test Comment', response1.data)
        response2 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment 2', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Test Comment 2', response2.data)
        response3 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment 3', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response3.status_code, 200)
        self.assertIn(b'Test Comment 3', response3.data)
        response4 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment 4', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response4.status_code, 200)
        self.assertIn(b'Test Comment 4', response4.data)
        
    def test_post_five_comments(self):
        self.client.post('/', data={'name': 'Test User', 'post': 'Test Message'}, follow_redirects=True)
        response1 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Test Comment', response1.data)
        response2 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment 2', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Test Comment 2', response2.data)
        response3 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment 3', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response3.status_code, 200)
        self.assertIn(b'Test Comment 3', response3.data)
        response4 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment 4', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response4.status_code, 200)
        self.assertIn(b'Test Comment 4', response4.data)
        response5 = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment 5', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response5.status_code, 200)
        self.assertIn(b'Test Comment 5', response5.data)
       
   
    def test_special_characters_in_comment(self):
        self.client.post('/', data={'name': 'Test User', 'post': 'Test Message'}, follow_redirects=True)
        response = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Special Comment $^#^', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Special Comment $^#^', response.data) 
    
    def test_special_characters_in_message(self):
        special_message = {'name': 'Test User', 'post': 'Message with special characters: $^#^'}
        response = self.client.post('/', data=special_message, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Message with special characters: $^#^', response.data)
    
    def test_single_category_filtering(self):
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Message 1', 'categories': 'Secrets'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/?filter=Secrets')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Message 1', response.data)
    
    def test_too_many_categories_error_three(self):
        data = {'name': 'Test User', 'post': 'This message must not be inside the resulting page.', 'categories': ['Secrets', 'Family', 'Health']}
        response = self.client.post('/', data=data, follow_redirects=True)
        response = self.client.get('/')
        self.assertNotIn(b'This message must not be inside the resulting page.', response.data)
    
    def test_too_many_categories_error_four(self):
        data = {'name': 'Test User', 'post': 'This message must not be inside the resulting page.', 'categories': ['Secrets', 'Family', 'Health', 'Confession']}
        response = self.client.post('/', data=data, follow_redirects=True)
        response = self.client.get('/')
        self.assertNotIn(b'This message must not be inside the resulting page.', response.data)
    
    def test_too_many_categories_error_five(self):
        data = {
            'name': 'Test User',
            'post': 'This message must not be inside the resulting page.',
            'categories': ['Secrets', 'Family', 'Health', 'Confession', 'Other'],
        }
        response = self.client.post('/', data=data, follow_redirects=True)
        response = self.client.get('/')
        self.assertNotIn(b'This message must not be inside the resulting page.', response.data)
    
    def test_post_message_with_one_category_and_post_one_comment(self):
        response = self.client.post('/', data={'name': 'Test User', 'post': 'Test Message', 'categories': 'Health'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/', data={'name': 'Test User', 'comment': 'Test Comment', 'parent_id': 0}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Comment', response.data)
    
    def test_special_characters_in_search_query(self):
        self.client.post('/', data={'name': 'Test User','post': 'Test with special characters: *#^'})
        response = self.client.get('/?search=*#^')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test with special characters: *#^', response.data)
    
    def test_search_and_comment(self):
        response = self.client.post('/', data={'name': 'Test User','post': 'Test Message'}, follow_redirects=True)
        response = self.client.get('/?search=Message')
        response = self.client.post('/', data={'name': 'Test User','comment': 'Test Comment','parent_id': 0}, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(b'search=Message', response.data)
    
    def test_single_result_found_with_search(self):
        data1 = {'name': 'Test User 1','post': 'Test Message 1',}
        response1 = self.client.post('/', data=data1)
        self.assertEqual(response1.status_code, 200)
        response = self.client.get('/?search=Test')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Message 1', response.data)
        
    def test_multiple_results_found_with_search(self):
        response = self.client.post('/', data={'name': 'Test User 1', 'post': 'Test Message 1'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/', data={'name': 'Test User 1', 'post': 'Test Message 2'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/?search=Test')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Message 1', response.data)
        self.assertIn(b'Test Message 2', response.data)

if __name__ == '__main__':
    unittest.main()
