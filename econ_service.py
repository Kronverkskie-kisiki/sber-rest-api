# econ_service.py
import grpc
from concurrent import futures
import time
import check_pb2
import check_pb2_grpc


class EconService(check_pb2_grpc.ValidationServiceServicer):
    def ProcessData(self, request, context):
        # Process data received from the first microservice
        # data = request.data
        # Perform some computation or processing
        result_data = {
            "passport": False,
            "registration": False,
            "residence": False,
            "presence_of_children": False,
            "job": False,
            "salary": False,
            "bride_price": False,
            "saving": False,
        }

        return check_pb2.ValidationResponse(**result_data)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    check_pb2_grpc.add_ValidationServiceServicer_to_server(EconService(), server)
    server.add_insecure_port("[::]:5001")
    server.start()
    print("EconService started.")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
