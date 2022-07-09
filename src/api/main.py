from flask import Flask
from flask_restx import Api, Resource, fields  # type: ignore

from subprocess import Popen, PIPE
from typing import List, Tuple

import pprint
import json
import codecs

app = Flask(__name__)
api = Api(
    app,
    version="1.0",
    title="YC Docker API",
    description="YC Docker Api",
)

ns = api.namespace("api", description="YC Docker Api")

todo = api.model(
    "Todo",
    {
        "id": fields.Integer(readonly=True, description="The task unique identifier"),
        "task": fields.String(required=True, description="The task details"),
    },
)

Container = api.model(
    "Container",
    {
        "Command": fields.String(required=True, description="Command"),
        "CreatedAt": fields.String(required=True, description="Created At"),
        "ID": fields.String(required=True, description="Container ID"),
        "Image": fields.String(required=True, description="Image Name"),
        "Labels": fields.String(required=True, description="Labels"),
        "LocalVolumes": fields.String(required=True, description="Local Volumes"),
        "Mounts": fields.String(required=True, description="Mounts"),
        "Names": fields.String(required=True, description="Names"),
        "Networks": fields.String(required=True, description="Networks"),
        "Ports": fields.String(required=True, description="Ports"),
        "RunningFor": fields.String(required=True, description="RunningFor"),
        "Size": fields.String(required=True, description="Size"),
        "State": fields.String(required=True, description="State"),
        "Status": fields.String(required=True, description="Status"),
    },
)


class Environment:
    def __init__(self):
        pass


class YCDockerApi:
    def __init__(self):
        pass

    def __run(self, cmd: List) -> Tuple[str, str]:
        with Popen(cmd, stdout=PIPE, stderr=PIPE) as proc:
            stdout = (
                bytes(proc.stdout.read()).decode("utf8")
                if proc.stdout is not None
                else ""
            )
            stderr = (
                bytes(proc.stderr.read()).decode("utf8")
                if proc.stderr is not None
                else ""
            )
            return stdout, stderr

    def list(self):
        cmd = [
            "docker",
            "ps",
            "--format",
            "{{ json . }}",
            "--no-trunc",
        ]
        stdout, stderr = self.__run(cmd)

        containers = []
        for line in stdout.splitlines():
            container = json.loads(line)
            containers.append(container)

        return containers

    def up(self, env: str):
        pass


DockerApi = YCDockerApi()


class TodoDAO(object):
    def __init__(self):
        self.counter = 0
        self.todos = []

    def get(self, id):
        for todo in self.todos:
            if todo["id"] == id:
                return todo
        api.abort(404, "Todo {} doesn't exist".format(id))

    def create(self, data):
        todo = data
        todo["id"] = self.counter = self.counter + 1
        self.todos.append(todo)
        return todo

    def update(self, id, data):
        todo = self.get(id)
        todo.update(data)
        return todo

    def delete(self, id):
        todo = self.get(id)
        self.todos.remove(todo)


DAO = TodoDAO()


@ns.route("/")
class NotFound(Resource):
    @ns.doc("Not Found")
    def get(self):
        return ""


@ns.route("/containers")
class ContainersList(Resource):
    @ns.doc("list_containers")
    @ns.marshal_list_with(Container)
    def get(self):
        """List all containers running"""
        return DockerApi.list()


@ns.route("/<int:id>")
@ns.response(404, "Todo not found")
@ns.param("id", "The task identifier")
class Todo(Resource):
    """Show a single todo item and lets you delete them"""

    @ns.doc("get_todo")
    @ns.marshal_with(todo)
    def get(self, id):
        """Fetch a given resource"""
        return DAO.get(id)

    @ns.doc("delete_todo")
    @ns.response(204, "Todo deleted")
    def delete(self, id):
        """Delete a task given its identifier"""
        DAO.delete(id)
        return "", 204

    @ns.expect(todo)
    @ns.marshal_with(todo)
    def put(self, id):
        """Update a task given its identifier"""
        return DAO.update(id, api.payload)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
