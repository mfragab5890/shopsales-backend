import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = 'trivia_test'
        setup_db(self.app, self.database_name)

        self.new_question = {
            'question': 'who won the us elections 2020?',
            'answer': 'Joe Biden',
            'difficulty': 3,
            'category': 4
        }
        self.new_question_2 = {
            'question': 'who won the us elections 2020?',
            'answer': 'Joe Biden',
            'difficulty': 3,
        }
        self.search_1 = {
            'searchTerm': 'a'
        }
        self.search_2 = {
            'searchTerm': 'Pneumonoultramicroscopicsilicovolcanoconiosis'
        }
        self.category_1 = {
            'category': 1
        }
        self.category_2 = {
            'category': 10
        }
        self.quiz_1 = {
            'previousQuestions': [ 20 ],
            'category': 1
        }
        self.quiz_2 = {
            'previousQuestions': [ 20 ],
            'category': 10
        }
        self.quiz_3 = {
            'previousQuestions': [ 20 ],
            'category': 'All'
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all(app=create_app())

    def tearDown(self):
        """Executed after reach test"""
        pass

    # test get all questions if exist
    def test_get_questions_per_page(self):
        """Test if all questions returned from database call and set to pages """
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data[ 'success' ], True)
        self.assertTrue(data[ 'total_questions' ])
        self.assertTrue(len(data[ 'categories' ]))

    # test get questions where page nonexistent or database empty
    def test_error_questions_on_page_not_exist(self):
        """Test that calling an nonexistent page will abort 404 """
        res = self.client().get('/questions?page=1000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data[ 'success' ], False)
        self.assertEqual(data[ 'error' ], 404)
        self.assertEqual(data[ 'message' ], 'Not found!!! : please check your Data or maybe your request is currently '
                                            'not available.')

    # test get questions where category nonexistent or database empty
    def test_error_questions_on_category_not_exist(self):
        """Test that calling an nonexistent category will abort 404 """
        res = self.client().get('/questions?category=1000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data[ 'success' ], False)
        self.assertEqual(data[ 'error' ], 404)
        self.assertEqual(data[ 'message' ],
                         'Not found!!! : please check your Data or maybe your request is currently '
                         'not available.')

    # test get all categories if exist
    def test_get_all_categories(self):
        """Test if all categories returned from database call and set to pages """
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data[ 'success' ], True)
        self.assertTrue(data[ 'total_categories' ])
        self.assertTrue(len(data[ 'categories' ]))

    # test get categories where an unknown argument is passed
    def test_error_categories_on_passing_invalid_argument(self):
        """Test that calling invalid url where false arguments passed will abort 404 """
        res = self.client().get('/categories/2')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data[ 'success' ], False)
        self.assertEqual(data[ 'error' ], 404)
        self.assertEqual(data[ 'message' ],
                         'Not found!!! : please check your Data or maybe your request is currently not available.')

    # test for delete question by passing id
    def test_check_deleted_question(self):
        res = self.client().delete('/questions/1')
        data = json.loads(res.data)

        question = Question.query.filter_by(id=1).first()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data[ 'success' ], True)
        self.assertEqual(data[ 'deleted_question' ], 1)
        self.assertTrue(data[ 'total_questions' ])
        self.assertTrue(len(data[ 'current_questions' ]))
        self.assertEqual(question, None)

    # check if error status code and error handeling works fine with trying to delete nonexistent question.
    def test_error_deleting_nonexistent_question(self):
        res = self.client().delete('/questions/1000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data[ 'success' ], False)
        self.assertEqual(data[ 'message' ],
                         'Unprocessable!!! : The request was well-formed but was unable to be followed')

    # test post a new question to database
    def test_add_user_question(self):
        """Test if user add a question it will be added successfully """
        res = self.client().post('/questions', json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data[ 'success' ], True)
        self.assertTrue(data[ 'created' ])
        self.assertTrue(len(data[ 'questions' ]))
        self.assertTrue(data[ 'total_questions' ])

    # test error while posting a new question to database with missing data
    def test_error_add_user_question(self):
        """Test if user if error will occur on user submit wrong data """
        res = self.client().post('/questions', json=self.new_question_2)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data[ 'success' ], False)
        self.assertEqual(data[ 'message' ],
                         'Unprocessable!!! : The request was well-formed but was unable to be followed')

    # test search question and return results
    def test_search_user_question(self):
        """Test if user search questions return results successfully """
        res = self.client().post('/questions/search', json=self.search_1)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data[ 'success' ], True)
        self.assertTrue(data[ 'search_term' ])
        self.assertTrue(len(data[ 'questions' ]))
        self.assertTrue(data[ 'total_questions' ])

    # test searching question with a string not found in database questions
    def test_error_searching_user_question(self):
        """Test if user search a question with non existent string will cause an error """
        res = self.client().post('/questions/search', json=self.search_2)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data[ 'success' ], False)
        self.assertEqual(data[ 'message' ],
                         'Unprocessable!!! : The request was well-formed but was unable to be followed')

    # test get questions by category and return results
    def test_get_user_category_question(self):
        """ Test if query category questions return results successfully """
        res = self.client().post('category/questions', json=self.category_1)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data[ 'success' ], True)
        self.assertTrue(data[ 'total_category_questions' ])
        self.assertTrue(len(data[ 'questions' ]))
        self.assertTrue(data[ 'current_category' ])

    # test get questions with invalid category will raise an error
    def test_error_searching_user_question(self):
        """Test if user search a category that don't exist will cause an error """
        res = self.client().post('category/questions', json=self.category_2)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data[ 'success' ], False)
        self.assertEqual(data[ 'message' ],
                         'Not found!!! : please check your Data or maybe your request is currently not available.')

    # test get quiz question by any category and return results
    def test_get_quiz_category_questions(self):
        """ Test if query a category return questions with no duplication for quiz """
        res = self.client().post('category/quiz/questions', json=self.quiz_1)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data[ 'success' ], True)
        self.assertTrue(data[ 'total_category_questions' ])
        self.assertTrue(len(data[ 'question' ]))

    # test get quiz question by all category and return results
    def test_get_quiz_all_categories_questions(self):
        """ Test if query return questions with no duplication for quiz of all categories """
        res = self.client().post('category/quiz/questions', json=self.quiz_3)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data[ 'success' ], True)
        self.assertTrue(data[ 'total_category_questions' ])
        self.assertTrue(len(data[ 'question' ]))

    # test get quiz question with invalid category will raise an error
    def test_error_get_user_quiz_question(self):
        """Test if user search a category that don't exist will cause an error """
        res = self.client().post('category/quiz/questions', json=self.quiz_2)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data[ 'success' ], False)
        self.assertEqual(data[ 'message' ],
                         'Not found!!! : please check your Data or maybe your request is currently not available.')


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
