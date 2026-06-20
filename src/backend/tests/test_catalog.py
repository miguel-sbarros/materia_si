"""GET /courses — dados de referência (filtro do quadro + seletor de turma). Critério 1."""

from tests.factories import make_course


def test_list_courses(api_client, db_session):
    make_course(db_session, name="Imersão", n_cohorts=2)
    make_course(db_session, name="Master 3.0", price="22250.00", n_cohorts=1)

    resp = api_client.get("/courses")
    assert resp.status_code == 200

    by_name = {c["name"]: c for c in resp.json()}
    assert {"Imersão", "Master 3.0"} <= by_name.keys()
    assert len(by_name["Imersão"]["cohorts"]) == 2

    cohort = by_name["Imersão"]["cohorts"][0]
    assert {"id", "course_id", "name", "status", "price_per_slot"} <= cohort.keys()
