import datetime as dt
import pytest
import mongomock
from fastapi.testclient import TestClient
import main  

client = TestClient(main.app)


mongo_client = mongomock.MongoClient()
database = mongo_client["practica1"]
mock_collection = database["historial"]


def setup_function():
    
    mock_collection.delete_many({})



def post_json(path: str, payload: dict):
    return client.post(path, json=payload)



@pytest.mark.parametrize(
    "path, a, b, expected",
    [
        ("/calculadora/sum", 2, 3, 5),
        ("/calculadora/sub", 10, 3, 7),
        ("/calculadora/mul", 4, 2.5, 10.0),
        ("/calculadora/div", 10, 2, 5.0),
    ],
)
def test_operaciones_ok(monkeypatch, path, a, b, expected):
    
    monkeypatch.setattr(main, "collection_historial", mock_collection)

    res = post_json(path, {"a": a, "b": b})
    assert res.status_code == 200
    data = res.json()
    assert data["a"] == pytest.approx(float(a))
    assert data["b"] == pytest.approx(float(b))
    assert data["resultado"] == pytest.approx(float(expected))

    
    saved = mock_collection.find_one({"a": float(a), "b": float(b)})
    assert saved is not None
    assert saved["resultado"] == pytest.approx(float(expected))
    assert saved["operacion"] in {"sum", "sub", "mul", "div"}
    assert isinstance(saved["date"], dt.datetime)



def test_division_cero_403(monkeypatch):
    monkeypatch.setattr(main, "collection_historial", mock_collection)

    res = post_json("/calculadora/div", {"a": 10, "b": 0})
    assert res.status_code == 403
    detail = res.json()["detail"]
    assert detail["error"] == "Division entre cero"
    assert detail["operacion"] == "div"
    assert detail["operandos"] == [10.0, 0.0]


@pytest.mark.parametrize(
    "path",
    [
        "/calculadora/sum",
        "/calculadora/sub",
        "/calculadora/mul",
        "/calculadora/div",
    ],
)
def test_no_negativos_400(monkeypatch, path):
    monkeypatch.setattr(main, "collection_historial", mock_collection)

    res = post_json(path, {"a": -1, "b": 2})
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert detail["error"] == "No se permiten números negativos"
    assert "operacion" in detail
    assert "operandos" in detail



def test_historial_devuelve_documentos(monkeypatch):
    monkeypatch.setattr(main, "collection_historial", mock_collection)

    
    docs = [
        {
            "a": 1.0,
            "b": 2.0,
            "resultado": 3.0,
            "operacion": "sum",
            "date": dt.datetime(2025, 10, 1, 0, 0, tzinfo=dt.timezone.utc),
        },
        {
            "a": 10.0,
            "b": 4.0,
            "resultado": 6.0,
            "operacion": "sub",
            "date": dt.datetime(2025, 10, 1, 1, 0, tzinfo=dt.timezone.utc),
        },
    ]
    mock_collection.insert_many(docs)

    res = client.get("/calculadora/historial")
    assert res.status_code == 200
    body = res.json()
    assert "historial" in body
    hist = body["historial"]
    assert len(hist) >= 2

    
    for item in hist:
        assert set(item.keys()) == {"a", "b", "resultado", "date", "operacion"}
        dt.datetime.fromisoformat(item["date"].replace("Z", "+00:00"))



def test_batch_ok(monkeypatch):
    monkeypatch.setattr(main, "collection_historial", mock_collection)
    payload = [
        {"op": "sum", "nums": [2, 4]},
        {"op": "mul", "nums": [2, 5]},
        {"op": "sub", "nums": [10, 3, 2]},
        {"op": "div", "nums": [100, 5, 2]},
    ]
    res = client.post("/calculadora/batch", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list) and len(data) == 4
    ops = {x["op"] for x in data}
    assert ops == {"sum", "mul", "sub", "div"}


def test_batch_div_zero_error(monkeypatch):
    monkeypatch.setattr(main, "collection_historial", mock_collection)
    payload = [{"op": "div", "nums": [10, 0]}]
    res = client.post("/calculadora/batch", json=payload)
    assert res.status_code == 403
    detail = res.json()["detail"]
    assert detail["error"] == "Division entre cero"
    assert detail["operacion"] == "div"
    assert detail["operandos"] == [10.0, 0.0]
