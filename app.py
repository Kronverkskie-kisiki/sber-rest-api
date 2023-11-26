from typing import Any, Dict
from flask import Flask, jsonify, request
import grpc
import check_pb2
import check_pb2_grpc
from enum import Enum
import requests

app = Flask(__name__)

STATUS_OK = "OK"
STATUS_WARN = "WARN"
STATUS_ERROR = "ERROR"

APP_PORT = 5005
APP_HOST = "0.0.0.0"

MICROSERVICE_GIGACHAT = "http://gigachat-api:5000"
MICROSERVICE_VK = "http://sber-vk-api:8080"

ECON_SERVICE_ADDRESS = "localhost:5001"


def send_data_to_econ_service(data):
    with grpc.insecure_channel(ECON_SERVICE_ADDRESS) as channel:
        stub = check_pb2_grpc.ValidationServiceStub(channel)
        response = stub.ProcessData(
            check_pb2.ValidationRequest(
                passport="1",
                registration="2",
                residence="3",
                presence_of_children="4",
                job="5",
                salary="6",
                bride_price="7",
                saving="8",
            )
        )
    return {
        "passport": response.passport,
        "registration": response.registration,
        "residence": response.residence,
        "presence_of_children": response.presence_of_children,
        "job": response.job,
        "salary": response.salary,
        "bride_price": response.bride_price,
        "saving": response.saving,
    }


def doubtful_ok(value: Any):
    return {"value": value, "status": STATUS_OK}


def doubtful_warn(value: Any, message: str):
    return {"value": value, "status": STATUS_WARN, "message": message}


def doubtful_error(value: Any, message: str):
    return {"value": value, "status": STATUS_ERROR, "message": message}


class CreditHistoryStatus(str, Enum):
    NONE = "NONE"
    BAD = "BAD"
    MEDIUM = "MEDIUM"
    GOOD = "GOOD"


class MainIncomeType(str, Enum):
    MAIN_WORK = "MAIN_WORK"
    BUSINESS = "BUSINESS"
    PENSION = "PENSION"
    OTHER = "OTHER"


class MaritalStatus(str, Enum):
    SINGLE = "SINGLE"
    MARRIED = "MARRIED"
    DIVORCED = "WIDOW"


def risk(number: int, param: Any):
    return {"scorePoints": number, "value": param}


def calculate_risks(id: str) -> dict[str, Any]:
    risks = {
        "id": id,
        "marital_status": risk(3, MaritalStatus.SINGLE),
        "have_children": risk(5, True),
        "credit_history": risk(1, CreditHistoryStatus.GOOD),
        "main_income_type": risk(2, MainIncomeType.MAIN_WORK),
        "current_job_seniority": risk(3, 4),
        "debt_burden_indicator": risk(3, 0.2),
        "total_income": risk(7, 50000),
        "have_savings_account": risk(3, 1),
    }
    return risks


def validate_personal_info(id: str):
    profile_data = {
        "id": "123",
        "firstName": {"value": "John", "status": "OK"},
        "secondName": {"value": "Doe", "status": "OK"},
        "middleName": {"value": "Smith", "status": "OK"},
        "birthDate": {"value": "1990-01-01", "status": "OK"},
        "passSeries": {"value": "AB", "status": "WARN"},
        "passNumber": {"value": "123456", "status": "OK"},
        "registrationAddress": {"value": "123 Main St", "status": "OK"},
        "residenceAddress": {"value": "456 Oak St", "status": "OK"},
        "maritalStatus": {"value": "MARRIED", "status": "OK"},
        "haveChildren": {"value": True, "status": "OK"},
        "jopPlace": {"value": "ABC Corporation", "status": "OK"},
        "jobExperience": {"value": "5 years", "status": "OK"},
        "jobPosition": {"value": "Software Engineer", "status": "OK"},
        "monthOfficialIncome": {"value": 5000, "status": "OK"},
        "incomeDocument": {"value": "Paystub", "status": "OK"},
        "monthAdditionalIncome": {"value": 1000, "status": "OK"},
        "isAdditionalIncomeApproved": {"value": True, "status": "OK"},
        "additionalIncomeSource": {"value": "Freelancing", "status": "OK"},
        "haveBankSavings": {"value": True, "status": "OK"},
    }
    profile_data_wrong = {
        "id": "123",
        "firstName": doubtful_ok("John"),
        "secondName": doubtful_ok("Doe"),
        "middleName": doubtful_ok("Smith"),
        "birthDate": doubtful_warn(2022, "Очень молодой"),
        "passSeries": doubtful_warn("47", "Не совпадает с датой рождения"),
        "passNumber": doubtful_ok(12234),
        "registrationAddress": doubtful_ok("Moscow"),
        "residenceAddress": doubtful_error("Alpha-Centauri", "Не существующее место"),
        "maritalStatus": doubtful_ok("MARRIED"),
        "haveChildren": doubtful_ok(False),
        "jopPlace": doubtful_ok("OOO Vasilyok"),
        "jobExperience": doubtful_error("-3 years", "Negative experience"),
        "jobPosition": doubtful_ok("Manager"),
        "monthOfficialIncome": doubtful_ok(100000),
        "incomeDocument": doubtful_ok("2-НДФЛ"),
        "monthAdditionalIncome": doubtful_warn(42069, "Нет подтверждения"),
        "isAdditionalIncomeApproved": doubtful_warn(False, "Не подтвержденный доход"),
        "additionalIncomeSource": doubtful_ok("Фриланс"),
        "haveBankSavings": doubtful_warn(False, "Не имеет сбережений"),
    }
    return [profile_data_wrong]


@app.route("/api/get_risk_info", methods=["GET"])
def get_risk_info():
    id = request.args.get("id")
    if id is None:
        return jsonify({"error": "Id not provided in request args"}), 500

    return jsonify(calculate_risks(id))


@app.route("/api/get_profile_info", methods=["GET"])
def get_profile_info():
    id = request.args.get("id")
    data_to_send = {"key": "value"}

    # Send data to the second microservice
    econ_response = send_data_to_econ_service(data_to_send)
    app.logger.info(econ_response)

    if id is None:
        return jsonify({"error": "Id not provided in request args"}), 500

    return jsonify(validate_personal_info(id))


@app.route("/api/loan_rating", methods=["POST"])
def loan_rating():
    response = requests.post(MICROSERVICE_GIGACHAT + "/api/loan_rating")
    response.raise_for_status()
    json_rpc_response = response.json()
    app.logger.info(json_rpc_response)
    return jsonify(json_rpc_response)


@app.route("/api/vk_friends", methods=["POST"])
def vk_friends():
    vk_id = request.get_json().get("userId")
    friends = requests.get(MICROSERVICE_VK + "/api/v1/vk/get_friends/" + vk_id)
    friends.raise_for_status()
    response = requests.post(
        MICROSERVICE_GIGACHAT + "/api/vk_friends",
        json={"friends_info": friends.content.decode("utf-8")},
    )
    response.raise_for_status()
    json_rpc_response = response.json()
    return jsonify(json_rpc_response)


@app.route("/api/vk_analisis", methods=["POST"])
def vk_analisis():
    vk_id = request.get_json().get("userId")
    friends = requests.get(MICROSERVICE_VK + "/api/v1/vk/get_profile/" + vk_id)
    friends.raise_for_status()
    response = requests.post(
        MICROSERVICE_GIGACHAT + "/api/vk_analisis",
        json={"profile_info": friends.content.decode("utf-8")},
    )
    response.raise_for_status()
    json_rpc_response = response.json()
    return jsonify(json_rpc_response)


if __name__ == "__main__":
    app.run(host=APP_HOST, port=APP_PORT, debug=True)
