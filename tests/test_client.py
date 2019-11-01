import copy
import io

import pytest
import requests

import tdworkflow
from tdworkflow import exceptions
from tdworkflow.attempt import Attempt
from tdworkflow.client import Client
from tdworkflow.log import LogFile
from tdworkflow.project import Project
from tdworkflow.revision import Revision
from tdworkflow.schedule import Schedule, ScheduleAttempt
from tdworkflow.session import Session
from tdworkflow.workflow import Workflow


def test_create_client():
    client = Client(site="us", apikey="APIKEY")
    assert client.site == "us"
    assert client.endpoint == "api-workflow.treasuredata.com"
    assert client.apikey == "APIKEY"
    assert isinstance(client.http, requests.Session)
    assert client.http.headers["Authorization"] == "TD1 APIKEY"
    assert client.http.headers["User-Agent"] == f"tdworkflow/{tdworkflow.__version__}"
    assert client.api_base == "https://api-workflow.treasuredata.com/api/"


def test_create_client_with_endpoint():
    client = Client(endpoint="digdag.example.com", apikey="APIKEY")
    assert client.site == "us"
    assert client.endpoint == "digdag.example.com"
    assert client.apikey == "APIKEY"
    assert isinstance(client.http, requests.Session)
    assert client.http.headers["Authorization"] == "TD1 APIKEY"
    assert client.http.headers["User-Agent"] == f"tdworkflow/{tdworkflow.__version__}"
    assert client.api_base == "https://digdag.example.com/api/"


RESP_DATA_GET_0 = {
    "projects": [
        {
            "id": "115819",
            "name": "pandas-df",
            "revision": "c53fa6f9117c491bac024d693332ccf5",
            "createdAt": "2019-07-17T04:48:45Z",
            "updatedAt": "2019-10-30T08:34:39Z",
            "deletedAt": None,
            "archiveType": "s3",
            "archiveMd5": "KruTqOtJ659HHpIJ6NyTTA==",
        }
    ]
}

RESP_DATA_GET_1 = {
    "workflows": [
        {
            "id": "1614347",
            "name": "pandas-df",
            "project": {"id": "115819", "name": "pandas-df"},
            "revision": "c53fa6f9117c491bac024d693332ccf5",
            "timezone": "UTC",
            "config": {
                "+read_into_df": {
                    "py>": "py_scripts.examples.read_td_table",
                    "database_name": "sample_datasets",
                    "table_name": "nasdaq",
                    "docker": {"image": "digdag/digdag-python:3.7"},
                    "_env": {
                        "TD_API_KEY": "${secret:td.apikey}",
                        "TD_API_SERVER": "${secret:td.apiserver}",
                    },
                },
                "+write_into_td": {
                    "py>": "py_scripts.examples.write_td_table",
                    "database_name": "pandas_test",
                    "table_name": "my_df",
                    "docker": {"image": "digdag/digdag-python:3.7"},
                    "_env": {
                        "TD_API_KEY": "${secret:td.apikey}",
                        "TD_API_SERVER": "${secret:td.apiserver}",
                    },
                },
            },
        }
    ]
}

RESP_DATA_GET_2 = {
    "revisions": [
        {
            "revision": "2a01a9ba-96a1-420a-851f-a1521f874493",
            "createdAt": "2019-11-01T05:34:15Z",
            "archiveType": "s3",
            "archiveMd5": "+sWKEpHPDe7DS81vcrO51Q==",
            "userInfo": {
                "td": {
                    "user": {
                        "id": 24446,
                        "name": "Michiaki Ariga",
                        "email": "ariga@treasure-data.com",
                    }
                }
            },
        }
    ]
}

RESP_DATA_GET_3 = {
    "schedules": [
        {
            "id": "23494",
            "project": {"id": "168037", "name": "python-tdworkflow"},
            "workflow": {"id": "1624118", "name": "simple"},
            "nextRunTime": "2019-11-01T07:00:00Z",
            "nextScheduleTime": "2019-11-01T00:00:00+00:00",
            "disabledAt": None,
        }
    ]
}

RESP_DATA_GET_4 = {
    "id": "23494",
    "project": {"id": "168037", "name": "python-tdworkflow"},
    "workflow": {"id": "1624118", "name": "simple"},
    "attempts": [],
}

RESP_DATA_GET_5 = {
    "sessions": [
        {
            "id": "14412528",
            "project": {"id": "113895", "name": "wf-performance-monitor"},
            "workflow": {"name": "wf-task-duration", "id": "1204939"},
            "sessionUuid": "b6af05c4-4875-48d1-9aed-8cbdf2104ae5",
            "sessionTime": "2019-11-01T08:03:00+00:00",
            "lastAttempt": {
                "id": "62497627",
                "retryAttemptName": None,
                "done": True,
                "success": True,
                "cancelRequested": False,
                "params": {
                    "last_session_time": "2019-11-01T08:00:00+00:00",
                    "next_session_time": "2019-11-01T08:06:00+00:00",
                    "last_executed_session_time": "2019-11-01T08:00:00+00:00",
                },
                "createdAt": "2019-11-01T08:03:00Z",
                "finishedAt": "2019-11-01T08:03:03Z",
            },
        }
    ]
}

RESP_DATA_GET_6 = {
    "attempts": [
        {
            "id": "62487260",
            "index": 1,
            "project": {"id": "168037", "name": "python-tdworkflow"},
            "workflow": {"name": "simple", "id": "1624118"},
            "sessionId": "14410781",
            "sessionUuid": "83dff830-5cff-427b-8647-4c5ab88cbb6f",
            "sessionTime": "2019-11-01T00:00:00+00:00",
            "retryAttemptName": None,
            "done": True,
            "success": True,
            "cancelRequested": False,
            "params": {
                "last_session_time": "2019-10-31T00:00:00+00:00",
                "next_session_time": "2019-11-02T00:00:00+00:00",
            },
            "createdAt": "2019-11-01T07:00:00Z",
            "finishedAt": "2019-11-01T07:06:38Z",
        }
    ]
}

RESP_DATA_GET_7 = {
    "files": [
        {
            "fileName": "+simple+simple_with_arg@example.com.log.gz",
            "fileSize": 161,
            "taskName": "+simple+simple_with_arg",
            "fileTime": "2019-11-01T07:00:22Z",
            "agentId": "8@ip-172-18-168-153.ec2.internal",
            "direct": "https://digdag.example.com/log/2019-11-01/XXXX",
        }
    ]
}

RESP_DATA_PUT_0 = {
    "id": "167272",
    "name": "python-tdworkflow",
    "revision": "1d4629f3-f4dd-4d17-82a0-6d0e23b291fa",
    "createdAt": "2019-10-30T14:05:34Z",
    "updatedAt": "2019-11-01T03:27:47Z",
    "deletedAt": None,
    "archiveType": "s3",
    "archiveMd5": "rYhVxGxbiyQxK+cbNNokHw==",
}

RESP_DATA_DELETE_0 = RESP_DATA_PUT_0


def prepare_mock(
    client,
    mocker,
    ret_val=None,
    status_code=200,
    side_effect=None,
    method="get",
    content=b"",
    mock=True,
    json=False,
):
    if mock:
        client._http = mocker.MagicMock()
    response = getattr(client._http, method).return_value
    response.status_code = status_code
    response.content = content
    if ret_val:
        response.json.return_value = ret_val
    if side_effect:
        response.raise_for_status.side_effect = side_effect
    if json:
        response.headers = {"Content-Type": "application/json"}


class TestProjectAPI:
    def setup_method(self, method):
        print("method{}".format(method.__name__))
        self.client = Client(site="us", apikey="APIKEY")

    def test_projects(self, mocker):
        prepare_mock(self.client, mocker, RESP_DATA_GET_0)

        pjs = self.client.projects()
        assert pjs == [Project(**p) for p in RESP_DATA_GET_0["projects"]]

        pj_name = RESP_DATA_GET_0["projects"][0]["name"]
        pjs2 = self.client.projects(name=pj_name)
        assert pjs2 == [Project(**p) for p in RESP_DATA_GET_0["projects"]]

    def test_project(self, mocker):
        prepare_mock(self.client, mocker, RESP_DATA_GET_0["projects"][0])

        pj = RESP_DATA_GET_0["projects"][0]
        assert Project(**pj) == self.client.project(int(pj["id"]))

    def test_nonexist_project(self, mocker):
        res = {
            "message": "Resource does not exist: project id=-1",
            "status": 404,
        }
        prepare_mock(self.client, mocker, res, 404, requests.exceptions.HTTPError())

        with pytest.raises(exceptions.HttpError):
            self.client.project(-1)

    def test_project_workflows(self, mocker):
        prepare_mock(self.client, mocker, RESP_DATA_GET_1)

        pj = RESP_DATA_GET_0["projects"][0]
        wfs = self.client.project_workflows(int(pj["id"]))
        assert [Workflow(**w) for w in RESP_DATA_GET_1["workflows"]] == wfs

    def test_create_project(self, mocker):
        prepare_mock(
            self.client,
            mocker,
            RESP_DATA_PUT_0,
            method="put",
            content=b"abc",
            json=True,
        )

        pj = self.client.create_project("test-project", "/tmp/foo")
        assert Project(**RESP_DATA_PUT_0) == pj

    def test_delete_project(self, mocker):
        prepare_mock(
            self.client,
            mocker,
            RESP_DATA_DELETE_0,
            status_code=204,
            method="delete",
            content=b"abc",
            json=True,
        )

        pj_id = RESP_DATA_GET_0["projects"][0]["id"]
        assert self.client.delete_project(int(pj_id)) is True

    def test_project_revisions(self, mocker):
        prepare_mock(self.client, mocker, RESP_DATA_GET_2)

        pj = RESP_DATA_GET_0["projects"][0]
        revs = self.client.project_revisions(int(pj["id"]))
        assert [Revision(**r) for r in RESP_DATA_GET_2["revisions"]] == revs

    def test_project_schedules(self, mocker):
        prepare_mock(self.client, mocker, RESP_DATA_GET_3)

        pj = RESP_DATA_GET_0["projects"][0]
        sches = self.client.project_schedules(int(pj["id"]))
        assert [Schedule(**s) for s in RESP_DATA_GET_3["schedules"]] == sches

    def test_set_secrets(self, mocker):
        prepare_mock(self.client, mocker, method="put")

        pj_id = RESP_DATA_GET_0["projects"][0]["id"]
        assert self.client.set_secrets(pj_id, {"test": "SECRET"})

    def test_secrets(self, mocker):
        content = b'{"secrets":[{"key":"foo"},{"key":"bar"}]}'
        ret_val = {"secrets": [{"key": "foo"}, {"key": "bar"}]}
        prepare_mock(self.client, mocker, ret_val=ret_val, content=content)

        pj_id = RESP_DATA_GET_0["projects"][0]["id"]
        assert self.client.secrets(int(pj_id)) == ["foo", "bar"]

    def test_delete_secret(self, mocker):
        content = b'{"secrets":[{"key":"foo"},{"key":"bar"}]}'
        ret_val = {"secrets": [{"key": "foo"}, {"key": "bar"}]}
        prepare_mock(self.client, mocker, ret_val=ret_val, content=content)

        prepare_mock(
            self.client,
            mocker,
            status_code=204,
            ret_val={"secrets": [{"key": "foo"}]},
            method="delete",
            mock=False,
        )

        pj_id = RESP_DATA_GET_0["projects"][0]["id"]
        assert self.client.delete_secret(int(pj_id), "foo") is True


class TestWorkflowAPI:
    def setup_method(self, method):
        print("method{}".format(method.__name__))
        self.client = Client(site="us", apikey="APIKEY")

    def test_workflows(self, mocker):
        prepare_mock(self.client, mocker, ret_val=RESP_DATA_GET_1)
        wfs = self.client.workflows()
        assert [Workflow(**w) for w in RESP_DATA_GET_1["workflows"]] == wfs

    def test_workflow(self, mocker):
        target_wf = RESP_DATA_GET_1["workflows"][0]
        prepare_mock(self.client, mocker, ret_val=target_wf)

        wf = self.client.workflow(int(target_wf["id"]))
        assert Workflow(**target_wf) == wf

    def test_unexist_workflow(self, mocker):
        prepare_mock(
            self.client,
            mocker,
            status_code=404,
            ret_val={
                "message": "Resource does not exist: workflow id=-1",
                "status": 404,
            },
            side_effect=requests.exceptions.HTTPError(),
        )

        with pytest.raises(exceptions.HttpError):
            self.client.workflow(-1)


class TestScheduleAPI:
    def setup_method(self, method):
        print("method{}".format(method.__name__))
        self.client = Client(site="us", apikey="APIKEY")

    def test_schedules(self, mocker):
        prepare_mock(self.client, mocker, ret_val=RESP_DATA_GET_3)

        sches = self.client.schedules()
        assert [Schedule(**s) for s in RESP_DATA_GET_3["schedules"]] == sches

    def test_schedule(self, mocker):
        sched = RESP_DATA_GET_3["schedules"][0]
        prepare_mock(self.client, mocker, ret_val=sched)

        assert Schedule(**sched) == self.client.schedule(int(sched["id"]))

    def test_backfill_schedule(self, mocker):
        prepare_mock(
            self.client,
            mocker,
            ret_val=RESP_DATA_GET_4,
            method="post",
            json=True,
            content=b"acb",
        )
        sched = RESP_DATA_GET_3["schedules"][0]

        s_attempt = self.client.backfill_schedule(
            int(sched["id"]), 12345, "2019-11-01T15:45:37.018124+00:00", dry_run=False
        )
        assert ScheduleAttempt(**RESP_DATA_GET_4) == s_attempt

    def test_disable_schedule(self, mocker):
        scheds = copy.deepcopy(RESP_DATA_GET_3)
        sched = scheds["schedules"][0]
        sched["disabledAt"] = "2019-11-01T07:37:51Z"
        prepare_mock(
            self.client, mocker, ret_val=sched, method="post", json=True, content=b"abc"
        )
        s = self.client.disable_schedule(int(sched["id"]))
        assert Schedule(**sched) == s
        assert s.disabled_at is not None

    def test_enbale_schedule(self, mocker):
        sched = RESP_DATA_GET_3["schedules"][0]
        prepare_mock(
            self.client, mocker, ret_val=sched, method="post", json=True, content=b"abc"
        )
        s = self.client.disable_schedule(int(sched["id"]))
        assert Schedule(**sched) == s
        assert s.disabled_at is None

    def test_skip_schedule(self, mocker):
        sched = RESP_DATA_GET_3["schedules"][0]
        prepare_mock(
            self.client, mocker, ret_val=sched, method="post", json=True, content=b"abc"
        )
        s = self.client.skip_schedule(int(sched["id"]))
        assert Schedule(**sched) == s


class TestSessionAPI:
    def setup_method(self, method):
        print("method{}".format(method.__name__))
        self.client = Client(site="us", apikey="APIKEY")

    def test_sessions(self, mocker):
        prepare_mock(self.client, mocker, ret_val=RESP_DATA_GET_5)
        s = self.client.sessions()
        assert [Session(**ss) for ss in RESP_DATA_GET_5["sessions"]] == s

    def test_session(self, mocker):
        session = RESP_DATA_GET_5["sessions"][0]
        prepare_mock(self.client, mocker, ret_val=session)
        s = self.client.session(int(session["id"]))
        assert Session(**session) == s

    def test_session_attempts(self, mocker):
        prepare_mock(self.client, mocker, ret_val=RESP_DATA_GET_6)
        session = RESP_DATA_GET_5["sessions"][0]
        a = self.client.session_attempts(int(session["id"]))
        assert [Attempt(**at) for at in RESP_DATA_GET_6["attempts"]] == a


class TestLogAPI:
    def setup_method(self, method):
        print("method{}".format(method.__name__))
        self.client = Client(site="us", apikey="APIKEY")

    def test_log_files(self, mocker):
        attempt = RESP_DATA_GET_6["attempts"][0]
        prepare_mock(self.client, mocker, ret_val=RESP_DATA_GET_7)
        files = self.client.log_files(int(attempt["id"]))
        assert [LogFile(**l) for l in RESP_DATA_GET_7["files"]] == files

    def test_log_file(self, mocker):
        import gzip

        attempt_id = int(RESP_DATA_GET_6["attempts"][0]["id"])
        file = RESP_DATA_GET_7["files"][0]

        dummy_file = io.BytesIO()
        with gzip.open(dummy_file, "wb") as f:
            f.write(b"abc")

        prepare_mock(self.client, mocker, ret_val=file, content=dummy_file.getvalue())
        f = self.client.log_file(attempt_id, file["fileName"])
        assert isinstance(f, str)