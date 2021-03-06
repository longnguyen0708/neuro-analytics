from flask import Blueprint, jsonify, request
from flask_restful import reqparse, Resource, Api, fields
from playhouse.shortcuts import model_to_dict

from models.user import *

UPLOAD_FOLDER = os.getcwd() + '/uploads'

user_fields = {
    'UserName': fields.String,
    'Password': fields.String,
    'EmailId': fields.String
}


class Login(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('email_id', required=True, help='email id is required', location=['form', 'json'])
        self.reqparse.add_argument('password', required=True, help='password is required', location=['form', 'json'])

    def post(self):
        args = self.reqparse.parse_args()
        print(args)
        try:
            if User.get(User.email_id == args['email_id']).password == args[
                'password']:  # and User.get(User.email_id == args['email_id']).Active == 'Active':
                return jsonify({'statusCode': 200, 'email_id': args['email_id']})
            else:
                return jsonify({'statusCode': 400})
        except DoesNotExist:
            return jsonify({'statusCode': 400})


class AdminLogin(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('email_id', required=True, help='email_id is required', location=['form', 'json'])
        self.reqparse.add_argument('password', required=True, help='password is required', location=['form', 'json'])

    def post(self):
        args = self.reqparse.parse_args()
        print(args)
        try:
            if Admin.get(Admin.email_id == args['email_id']).password == args['password']:
                return jsonify({'statusCode': 200, 'email_id': args['email_id']})
            else:
                return jsonify({'statusCode': 400})
        except DoesNotExist:
            return jsonify({'statusCode': 400})


class Register(Resource):
    '''This resource is used for  registering a user'''

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('username', required=True, help='username is required', location=['form', 'json'])
        self.reqparse.add_argument('password', required=True, help='password is required', location=['form', 'json'])
        self.reqparse.add_argument('email_id', required=True, help='email is required', location=['form', 'json'])

    def post(self):
        args = self.reqparse.parse_args()
        User.create(**args)
        return jsonify({'statusCode': 200, 'result': 'success'})


class UpdateProfile(Resource):
    '''This resource is used for  registering a user'''

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', required=True, help='name is required', location=['form', 'json'])
        self.reqparse.add_argument('gender', required=True, help='gender is required', location=['form', 'json'])
        self.reqparse.add_argument('date_of_birth', required=True, help='date of birth is required',
                                   location=['form', 'json'])
        self.reqparse.add_argument('telephone', required=True, help='telephone is required', location=['form', 'json'])
        self.reqparse.add_argument('password', required=True, help='password is required', location=['form', 'json'])
        self.reqparse.add_argument('email_id', required=True, help='email is required', location=['form', 'json'])
        self.reqparse.add_argument('location', required=True, help='location is required', location=['form', 'json'])

    def post(self):
        args = self.reqparse.parse_args()
        q = User.update(name=args['name'], gender=args['gender'], date_of_birth=args['date_of_birth'],
                        telephone=args['telephone'], password=args['password'],
                        location=args['location']).where(User.email_id == args['email_id'])
        q.execute()
        return jsonify({'statusCode': 200, 'result': 'success'})


class GetUserDetails(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('email_id', required=True, help='email id is required', location=['form', 'json'])

    def post(self):
        result = []
        args = self.reqparse.parse_args()
        userDetails = User.get(User.email_id == args['email_id'])

        return jsonify({'statusCode': 200, 'userInfo': json.dumps(model_to_dict(userDetails))});


class Upload(Resource):
    ''' This api end point is used for uploading the accelerometer reading file'''

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('email_id', required=True, help='email_id is required', location=['form', 'json'])
        self.reqparse.add_argument('readings', required=True, help='readings is required', location='json')


    def parse_csv_file(self,list_of_readings, result_id):

        dict_list = []
        try:
            for reading in list_of_readings:
                temp = AccelerationUtil(**reading).__dict__
                temp['result_id'] = result_id
                dict_list.append(temp)
        except Exception as e:
            pass
        return dict_list

    def post(self):

        args = self.reqparse.parse_args()
        readings = request.get_json()['readings']
        email_id = args['email_id']
        # readings = args['readings']

        try:
            cursor = DATABASE.execute_sql(
                'select * from neuro_db.result where id = (select max(id) from neuro_db.result where email_id = %s)',
                email_id)
            my_dict = cursor.fetchone()

            if my_dict is None or len(my_dict) == 0:
                # insert the user
                result = Result(email_id=email_id)
                if result.save() == 1:
                    cursor = DATABASE.execute_sql(
                        'select * from neuro_db.result where id = (select max(id) from neuro_db.result where email_id = %s)',
                        email_id)
                    my_dict = cursor.fetchone()

            result_id = my_dict[0]

            list_of_objs = self.parse_csv_file(readings, result_id)

            with DATABASE.atomic():
                Acceleration.insert_many(list_of_objs).execute()

            return jsonify({'statusCode': 200, 'result': 'success'})
        except Exception as e:
            return jsonify({'statusCode': 500, 'result': str(e)})


class GetUserCurrentReport(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('email_id', required=True, help='email id is required', location=['form', 'json'])

    def post(self):
        args = self.reqparse.parse_args()

        user_current_result = Result.select().where(Result.email_id == args['email_id']).order_by(
            Result.date_taken.desc()).limit(1).get();
        print(user_current_result)
        return jsonify({'statusCode': 200, 'userInfo': json.dumps(model_to_dict(user_current_result), default=str)});


class GetUserReports(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('email_id', required=True, help='email id is required', location=['form', 'json'])

    def post(self):
        result = []
        args = self.reqparse.parse_args()

        q = Result.select().where(Result.email_id == args['email_id']);
        user_reports = q.execute();

        for report in user_reports:
            report_details = {}
            report_details['date_taken'] = report.date_taken
            report_details['accuracy'] = report.accuracy
            report_details['classification'] = report.classification
            report_details['model_name'] = report.model_name
            report_details['id'] = report.id

            result.append(report_details)
        print(result);
        return jsonify({'statusCode': 200, 'reports': result});


class GetAllUsers(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()

    def post(self):
        result = []
        args = self.reqparse.parse_args()
        users = User.select();

        for user in users:
            userInfo = {}
            userInfo['email_id'] = user.email_id;
            result.append(userInfo)

        return jsonify({'statusCode': 200, 'users': result});


login_api = Blueprint('resources.validate', __name__)

api = Api(login_api)
api.add_resource(Login, '/api/v1/validate', endpoint='login')
api.add_resource(Register, '/api/v1/register', endpoint='register')
api.add_resource(UpdateProfile, '/api/v1/updateProfile', endpoint='updateprofile')
api.add_resource(GetUserDetails, '/api/v1/getUserDetails', endpoint='getuserdetails')
api.add_resource(AdminLogin, '/api/v1/adminValidate', endpoint='adminlogin')
api.add_resource(Upload, '/api/v1/upload', endpoint='fileupload')
api.add_resource(GetUserCurrentReport, '/api/v1/getUserCurrentReport', endpoint='getusercurrentreport')
api.add_resource(GetUserReports, '/api/v1/getUserReports', endpoint='getuserreports')
api.add_resource(GetAllUsers, '/api/v1/getAllUsers', endpoint='getallusers')
