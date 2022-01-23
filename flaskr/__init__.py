from flask_cors import CORS
import dateutil.parser
import babel
from flask import Flask, request, jsonify, abort
from sqlalchemy import extract, or_
from math import ceil
from werkzeug.security import generate_password_hash, check_password_hash
from models import setup_db, Products, db, Orders, OrderItems, User, Permissions, UserPermissions
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required, \
    JWTManager


# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#
def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    setup_db(app, database_name)
    CORS(app)
    jwt = JWTManager(app)

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    # Refreshing tokens
    @app.after_request
    def refresh_expiring_jwts(response):
        try:
            exp_timestamp = get_jwt()[ "exp" ]
            now = datetime.now(timezone.utc)
            target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
            if target_timestamp > exp_timestamp:
                access_token = create_access_token(identity=get_jwt_identity())
            return response
        except (RuntimeError, KeyError):
            # Case where there is not a valid JWT. Just return the original respone
            return response

    # connection in configuration file added

    # ----------------------------------------------------------------------------#
    # Filters.
    # ----------------------------------------------------------------------------#

    def format_datetime(value, format='medium'):
        if isinstance(value, str):
            date = dateutil.parser.parse(value)
        else:
            date = value

        if format == 'full':
            format = "EEEE MMMM, d, y 'at' h:mma"
        elif format == 'medium':
            format = "EE MM, dd, y h:mma"
        return babel.dates.format_datetime(date, format, locale='en')

    app.jinja_env.filters[ 'datetime' ] = format_datetime

    # ----------------------------------------------------------------------------#
    # Initial Data.
    # ----------------------------------------------------------------------------#
    if User and Permissions and UserPermissions:
        # create admin user first time to run the app
        admin_user = User.query.get(1)
        if not admin_user:
            print('creating admin user')
            admin = User(
                id=1,
                username='admin',
                password_hash=generate_password_hash('adminADMIN', method='sha256'),
                email='m.f.ragab5890@gmail.com'
            )
            admin.insert()
            print('admin user created')

        # create seller user first time to run the app
        seller_user = User.query.get(2)
        if not seller_user:
            print('creating seller user')
            seller = User(
                id=2,
                username='seller',
                password_hash=generate_password_hash('sellerSELLER', method='sha256'),
                email='m.f.ragab581990@gmail.com'
            )
            seller.insert()
            print('seller user created')
        # create App permissions
        app_permissions_count = Permissions.query.count()
        if app_permissions_count < 1:
            permissions = [
                'CREATE_NEW_USER',
                'DELETE_USER',
                'CREATE_NEW_PRODUCT',
                'EDIT_PRODUCT',
                'GET_ALL_PRODUCTS',
                'SEARCH_PRODUCTS_BY_ID',
                'SEARCH_PRODUCTS_BY_TERM',
                'DELETE_PRODUCT',
                'CREATE_ORDER',
                'GET_MONTH_SALES',
                'GET_PERIOD_SALES',
                'GET_TODAY_SALES',
                'GET_USER_TODAY_SALES',
                'DELETE_ORDER',
            ]
            print('Creating Permessions')
            for permission in permissions:
                app_permission = Permissions(name=permission)
                try:
                    app_permission.insert()
                except Exception as e:
                    print(e)
            print('Permessions Created')
        # Add Permissions To Admin User
        app_permissions = Permissions.query.all()
        print('Adding Permissions to admin User')
        for permission in app_permissions:
            admin_permission_query = UserPermissions.query\
                .filter(UserPermissions.permission_id == permission.id) \
                .filter(UserPermissions.user_id == 1)\
                .first()
            if not admin_permission_query:
                admin_permission = UserPermissions(user_id=1, permission_id=permission.id, created_by=1)
                try:
                    admin_permission.insert()
                except Exception as e:
                    print('admin permission "', permission.name, '" adding error:', e)
        print('Permissions Added to admin User')
        # Add Permissions To Seller User
        app_permissions = Permissions.query.all()
        print('Adding Permissions to seller User')
        seller_permissions = [
            'SEARCH_PRODUCTS_BY_ID',
            'SEARCH_PRODUCTS_BY_TERM',
            'CREATE_ORDER',
            'GET_USER_TODAY_SALES',
        ]
        for permission in app_permissions:
            seller_permission_query = UserPermissions.query \
                .filter(UserPermissions.permission_id == permission.id) \
                .filter(UserPermissions.user_id == 2) \
                .first()
            if not seller_permission_query and permission.name in seller_permissions:
                seller_permission = UserPermissions(user_id=2, permission_id=permission.id, created_by=1)
                try:
                    seller_permission.insert()
                except Exception as e:
                    print('admin permission "', permission.name, '" adding error:', e)
        print('Permissions Added to seller User')
    # ----------------------------------------------------------------------------#
    # Controllers.
    # ----------------------------------------------------------------------------#

    @app.route('/', methods=[ 'GET' ])
    @jwt_required()
    def get_home_data():
        user_id = get_jwt_identity()
        try:
            user = User.query.get(user_id).format_no_password()
            user_permissions = [Permissions.query.get(user_permission['permission_id']).format() for user_permission in user['permissions'] ]
            user['permissions'] = user_permissions
            return jsonify({
                'success': True,
                'message': 'Welcome!' + user['username'],
                'authed_user': user,
            })
        except Exception as e:
            print(e)
            abort(400)

    # login endpoint no permission needed, takes username and password
    @app.route('/login', methods=[ 'POST' ])
    def login():
        body = request.get_json()
        username = body.get('username')
        password = body.get('password')
        remember = True if body.get('remember') else False

        user = User.query.filter(User.username == username).first()
        # check if the user actually exists
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        if not user or not check_password_hash(user.password_hash, password):
            response = jsonify({
                'success': False,
                'message': 'Username OR Password Are Not Correct',
            })
            unset_jwt_cookies(response)
            return response
        else:
            access_token = create_access_token(identity=user.id)
            user = user.format_no_password()
            user_permissions = [ Permissions.query.get(user_permission[ 'permission_id' ]).format() for user_permission
                                 in user[ 'permissions' ] ]
            user[ 'permissions' ] = user_permissions
            response = jsonify({
                'success': True,
                'message': 'User LoggedIn Correctly AS: ' + user['username'],
                'authed_user': user,
                'token': access_token,
            })
            return response

    @app.route('/user/new', methods=[ 'POST' ])
    @jwt_required()
    def signup():
        body = request.get_json()
        email = body.get('email')
        username = body.get('username')
        password = body.get('password')
        password_hash = generate_password_hash(password, method='sha256')
        # if this returns a user, then the username already exists in database
        user = User.query.filter(User.username == username).first()

        if user:  # if a user is found, we want to a message
            return jsonify({
                'success': False,
                'message': 'Username Already Exists',
            })
        # if this returns a user, then the email already exists in database
        user = User.query.filter(User.email == email).first()

        if user:  # if a user is found, we want to redirect back to signup page so user can try again
            return jsonify({
                'success': False,
                'message': 'Email Already Exists',
            })

        # create a new user with the form data. Hash the password so the plaintext version isn't saved.
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
        )
        try:
            new_user.insert()
            # get new list id
            user = Products.query \
                .filter(User.username == username) \
                .order_by(db.desc(User.id)).first().format()
            return jsonify({
                'success': True,
                'message': 'user created successfully',
                'newProduct': user,
            })
        except Exception as e:
            print(e)
            abort(400)

        # add the new user to the database

        return 'Signup'

    @app.route('/user/<int:user_id>', methods=[ 'DELETE' ])
    @jwt_required()
    def delete_user(user_id):
        if user_id != 1:
            user = User.query.get(user_id)
            try:
                user.delete()
                return jsonify({
                    'success': True,
                    'message': 'user of ID: ' + user_id + ' deleted successfully',
                })
            except Exception as e:
                print(e)
                abort(400)
        else:
            return jsonify({
                'success': True,
                'message': 'Warning! You Are Trying To Delete the Admin User This User Can Not Be Deleted',
            })

    @app.route('/logout', methods=[ 'GET' ])
    def logout():
        response = jsonify({
            'success': True,
            'message': 'logout Successful',
        })
        unset_jwt_cookies(response)
        return response

    # create new product endpoint. this end point should take:
    # name, sell_price, buy_price, qty, created_by, mini, maxi, sold, image, description
    # permission: CREATE_NEW_PRODUCT
    @app.route('/products/new', methods=[ 'POST' ])
    @jwt_required()
    def create_product():
        body = request.get_json()
        name = body.get('name', None)
        sell_price = int(body.get('sellingPrice', None))
        buy_price = int(body.get('buyingPrice', None))
        qty = int(body.get('quantity', 0))
        created_by = int(body.get('created_by', None))
        mini = int(body.get('minimum', 0))
        maxi = int(body.get('maximum', (qty + 1)))
        sold = int(body.get('sold', 0))
        image = body.get('image', '')
        description = body.get('description', None)

        new_product = Products(name=name,
                               sell_price=sell_price,
                               buy_price=buy_price,
                               qty=qty,
                               created_by=created_by,
                               mini=mini,
                               maxi=maxi,
                               sold=sold,
                               image=image,
                               description=description
                               )

        try:
            new_product.insert()
            # get new list id
            user_product = Products.query \
                .filter(Products.name == name) \
                .order_by(db.desc(Products.id)).first().format()
            return jsonify({
                'success': True,
                'message': 'product created successfully',
                'newProduct': user_product,
            })
        except Exception as e:
            print(e)
            abort(400)

    # edit product endpoint. this end point should take:
    # id and the details to be changed
    # permission: EDIT_PRODUCT
    @app.route('/products/edit', methods=[ 'PATCH' ])
    @jwt_required()
    def edit_product():
        body = request.get_json()
        product_id = int(body.get('id', None))
        if product_id is not None:
            user_product = Products.query.get(product_id)
            name = body.get('name', None)
            if name is not None:
                user_product.name = name
            sell_price = int(body.get('sellingPrice', None))
            if name is not None:
                user_product.name = name
            buy_price = int(body.get('buyingPrice', None))
            if name is not None:
                user_product.name = name
            qty = int(body.get('quantity', 0))
            if name is not None:
                user_product.name = name
            mini = int(body.get('minimum', 0))
            maxi = int(body.get('maximum', (qty + 1)))
            sold = int(body.get('sold', 0))
            image = body.get('image', '')
            description = body.get('description', None)

        new_product = Products(name=name,
                               sell_price=sell_price,
                               buy_price=buy_price,
                               qty=qty,
                               created_by=created_by,
                               mini=mini,
                               maxi=maxi,
                               sold=sold,
                               image=image,
                               description=description
                               )

        try:
            new_product.insert()
            # get new list id
            user_product = Products.query \
                .filter(Products.name == name) \
                .order_by(db.desc(Products.id)).first().format()
            return jsonify({
                'success': True,
                'message': 'product created successfully',
                'newProduct': user_product,
            })
        except Exception as e:
            print(e)
            abort(400)

    # get all products by page endpoint. this end point should take:
    # page as query parameter
    # permission: GET_ALL_PRODUCTS
    @app.route('/products/all/<int:page>', methods=[ 'GET' ])
    @jwt_required()
    def get_all_products(page):
        results_per_page = 33
        if not page:
            page = 1
        try:
            products_query = Products.query.order_by(db.desc(Products.id)).paginate(page, results_per_page,
                                                                                    False).items
            pages = round(ceil(Products.query.count() / results_per_page))
            products = [ product.format() for product in products_query ]
            return jsonify({
                'success': True,
                'products': products,
                'pages': pages,
            })
        except Exception as e:
            print(e)
            abort(400)

    # get product by id endpoint. this end point should take:
    # Product id as query parameter
    # permission: SEARCH_PRODUCTS_BY_ID
    @app.route('/products/search/id/<int:product_id>', methods=[ 'GET' ])
    @jwt_required()
    def search_products_id(product_id):
        try:
            data = Products.query.get(product_id)
            if data is not None:
                product = data.format()
                return jsonify(product)
            else:
                return jsonify({
                    "success": False,
                    "error": 400,
                    "message": "This Product Doesn't Exist In Your DataBase"
                })
        except Exception as e:
            print(e)
            abort(400)

    # get products by search term endpoint. this end point should take:
    # Search term as query parameter
    # permission: SEARCH_PRODUCTS_BY_TERM
    @app.route('/products/search/<string:search_term>', methods=[ 'GET' ])
    @jwt_required()
    def search_products_string(search_term):
        try:
            data = Products.query.filter(or_(
                Products.name.ilike('%' + search_term + '%'),
                Products.description.ilike('%' + search_term + '%'))) \
                .order_by(db.desc(Products.id)).all()
            if data is not None:
                products = [ product.format() for product in data ]
                return jsonify({
                    'success': True,
                    'products': products,
                })
            else:
                return jsonify({
                    "success": False,
                    "error": 400,
                    "message": "This Product Doesn't Exist In Your DataBase"
                })
        except Exception as e:
            print(e)
            abort(400)

    # delete product endpoint.this end point should take:
    # product id as query parameter
    # permission: DELETE_PRODUCT
    @app.route('/products/delete/<int:product_id>', methods=[ 'DELETE' ])
    @jwt_required()
    def delete_product(product_id):
        # check if user logged in and has permission
        if product_id is None:
            abort(400, 'No Product ID Entered')
        else:
            user_product = Products.query.get(product_id)
            if len(user_product.items) > 0:
                return jsonify({
                    'success': False,
                    'message': 'product can not be deleted as it is associated with other orders.'
                })
            else:
                try:
                    user_product.delete()

                    return jsonify({
                        'success': True,
                        'message': 'product deleted successfully'
                    })
                except Exception as e:
                    print(e)
                    abort(422)

    # create new order endpoint. this end point should take:
    # order items, user, total
    # permission: CREATE_ORDER
    @app.route('/orders/new', methods=[ 'POST' ])
    @jwt_required()
    def create_order():
        body = request.get_json()
        cart_items = body.get('cartItems', [ ])
        total_price = int(body.get('total', None))
        total_cost = int(body.get('totalCost', None))
        qty = int(body.get('totalQuantity', None))
        created_by = int(body.get('created_by', None))

        new_order = Orders(
            qty=qty,
            total_price=total_price,
            total_cost=total_cost,
            created_by=created_by,
        )

        try:
            new_order.insert()
            # get new list id
            user_order = Orders.query.order_by(db.desc(Orders.id)).first()
            for item in cart_items:
                qty = int(item[ 'quantity' ])
                total_price = int(item[ 'total' ])
                total_cost = int(item[ 'totalCost' ])
                order_id = int(user_order.id)
                product_id = int(item[ 'id' ])

                new_order_items = OrderItems(
                    qty=qty,
                    total_price=total_price,
                    total_cost=total_cost,
                    order_id=order_id,
                    product_id=product_id
                )
                user_product = Products.query.get(product_id)
                if isinstance(user_product.sold, int):
                    user_product.sold += qty
                else:
                    user_product.sold = qty

                if isinstance(user_product.qty, int):
                    user_product.qty -= qty
                else:
                    user_product.qty = 0
                try:
                    new_order_items.insert()
                    user_product.update()
                except Exception as e:
                    print(e)
                    abort(400)

            return jsonify({
                'success': True,
                'message': 'Order Added successfully',
                'order': user_order.format(),
            })
        except Exception as e:
            print(e)
            abort(400)

    # Get current month sales endpoint.
    # permission: GET_MONTH_SALES
    @app.route('/sales/month', methods=[ 'GET' ])
    @jwt_required()
    def get_month_orders():
        try:
            orders_query = Orders.query.filter(
                extract('year', Orders.created_on) == datetime.utcnow().year
            ).filter(
                extract('month', Orders.created_on) == datetime.utcnow().month
            ).order_by(db.desc(Orders.id)).all()
            orders = [ order.format() for order in orders_query ]
            return jsonify({
                'success': True,
                'orders': orders
            })
        except Exception as e:
            print(e)
            abort(400)

    # Get custom period sales endpoint.
    # permission: GET_PERIOD_SALES
    @app.route('/sales/period', methods=[ 'POST' ])
    @jwt_required()
    def get_period_orders():
        try:
            body = request.get_json()
            period_from = body.get('periodFrom', 0)
            period_to = body.get('periodTo', 0)
            period_to += ' 23:59:59.99999'
            orders_query = Orders.query.filter(
                Orders.created_on >= period_from,
                Orders.created_on <= period_to,
            ).order_by(db.desc(Orders.id)).all()
            orders = [ order.format() for order in orders_query ]
            return jsonify({
                'success': True,
                'orders': orders
            })
        except Exception as e:
            print(e)
            abort(400)

    # Get today sales endpoint.
    # permission: GET_TODAY_SALES
    @app.route('/sales/today', methods=[ 'GET' ])
    @jwt_required()
    def get_today_orders():
        try:
            orders_query = Orders.query.filter(
                extract('year', Orders.created_on) == datetime.utcnow().year
            ).filter(
                extract('month', Orders.created_on) == datetime.utcnow().month
            ).filter(
                extract('day', Orders.created_on) == datetime.utcnow().day
            ).order_by(db.desc(Orders.id)).all()
            orders = [ order.format() for order in orders_query ]
            return jsonify({
                'success': True,
                'orders': orders
            })
        except Exception as e:
            print(e)
            abort(400)

    # Get logged in user today sales endpoint.
    # permission: GET_USER_TODAY_SALES
    @app.route('/user/sales/today', methods=[ 'GET' ])
    @jwt_required()
    def get_user_today_orders():
        user_id = get_jwt_identity()
        try:
            orders_query = Orders.query\
                .filter(Orders.created_by == user_id)\
                .filter(extract('year', Orders.created_on) == datetime.utcnow().year)\
                .filter(extract('month', Orders.created_on) == datetime.utcnow().month)\
                .filter(extract('day', Orders.created_on) == datetime.utcnow().day)\
                .order_by(db.desc(Orders.id)).all()
            orders = [ order.format() for order in orders_query ]
            return jsonify({
                'success': True,
                'orders': orders
            })
        except Exception as e:
            print(e)
            abort(400)

    # delete orders endpoint.this end point should take:
    # order id as query parameter
    # permission: DELETE_ORDER
    @app.route('/orders/delete/<int:order_id>', methods=[ 'DELETE' ])
    @jwt_required()
    def delete_order(order_id):
        # check if user logged in and has permission
        if order_id is None:
            abort(400, 'No Order ID Entered')
        else:
            user_order = Orders.query.get(order_id)
            try:
                user_order.delete()

                return jsonify({
                    'success': True,
                    'message': 'order deleted successfully'
                })
            except Exception as e:
                abort(422)

    # ----------------------------------------------------------------------------#
    # Error Handlers.
    # ----------------------------------------------------------------------------#
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": 'Not found!!! : please check your Data or maybe your request is currently not available.'
        }), 404

    @app.errorhandler(422)
    def not_processable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": 'Unprocessable!!! : The request was well-formed but was unable to be followed'
        }), 422

    @app.errorhandler(405)
    def not_allowed_method(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": 'Method Not Allowed!!!: Your request method not supported by that API '
        }), 405

    @app.errorhandler(400)
    def not_good_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": 'Bad Request!!!! Please make sure the data you entered is correct'
        }), 400

    @app.errorhandler(500)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": 'Internal Server Error!!!: Please try again later or reload request. '
        }), 500

    return app
