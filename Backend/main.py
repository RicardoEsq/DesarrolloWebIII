import datetime
from fastapi import FastAPI, Body, HTTPException
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# jajajajajaj
mongo_client = MongoClient("mongodb://admin_user:web3@mongo:27017/")
database = mongo_client["practica1"]
collection_historial = database["historial"]


def _error_payload(msg: str, op: str, operandos):
    return {"error": msg, "operacion": op, "operandos": operandos}

def _validar_no_negativos(op: str, a: float, b: float):
    
    if a < 0 or b < 0:
        raise HTTPException(
            status_code=400,
            detail=_error_payload("No se permiten números negativos", op, [a, b]),
        )

def _guardar_historial(op: str, a: float, b: float, resultado):
    
    document = {
        "resultado": resultado,
        "a": a,
        "b": b,
        "operacion": op,
        "date": datetime.datetime.now(tz=datetime.timezone.utc),
    }
    collection_historial.insert_one(document)
    return document


@app.post("/calculadora/sum")
def sumar(payload: dict = Body(...)):
    a = float(payload.get("a"))
    b = float(payload.get("b"))
    _validar_no_negativos("sum", a, b)
    resultado = a + b
    _guardar_historial("sum", a, b, resultado)
    return {"a": a, "b": b, "resultado": resultado}

@app.post("/calculadora/sub")
def restar(payload: dict = Body(...)):
    a = float(payload.get("a"))
    b = float(payload.get("b"))
    _validar_no_negativos("sub", a, b)
    resultado = a - b
    _guardar_historial("sub", a, b, resultado)
    return {"a": a, "b": b, "resultado": resultado}

@app.post("/calculadora/mul")
def multiplicar(payload: dict = Body(...)):
    a = float(payload.get("a"))
    b = float(payload.get("b"))
    _validar_no_negativos("mul", a, b)
    resultado = a * b
    _guardar_historial("mul", a, b, resultado)
    return {"a": a, "b": b, "resultado": resultado}

@app.post("/calculadora/div")
def dividir(payload: dict = Body(...)):
    a = float(payload.get("a"))
    b = float(payload.get("b"))
    _validar_no_negativos("div", a, b)
    if b == 0:
        raise HTTPException(
            status_code=403,
            detail=_error_payload("Division entre cero", "div", [a, b]),
        )
    resultado = a / b
    _guardar_historial("div", a, b, resultado)
    return {"a": a, "b": b, "resultado": resultado}


@app.get("/calculadora/historial")
def obtener_historial(
    op: Optional[str] = None,                
    date_from: Optional[str] = None,         
    date_to: Optional[str] = None,           
    sort_by: Optional[str] = "date",         
    order: Optional[str] = "desc",           
):
    q = {}

    if op and op in {"sum", "sub", "mul", "div"}:
        q["operacion"] = op

    date_filter = {}

    def _parse_iso(s: str):
        try:
            s2 = s.replace("Z", "+00:00")
            return datetime.datetime.fromisoformat(s2)
        except Exception:
            return None

    if date_from:
        dt_from = _parse_iso(date_from)
        if dt_from:
            date_filter["$gte"] = dt_from
    if date_to:
        dt_to = _parse_iso(date_to)
        if dt_to:
            date_filter["$lte"] = dt_to
    if date_filter:
        q["date"] = date_filter

    sort_field = "date" if sort_by == "date" else "resultado"
    sort_dir = -1 if order == "desc" else 1

    operaciones = collection_historial.find(q).sort(sort_field, sort_dir)

    historial = []
    for operacion in operaciones:
        historial.append({
            "a": operacion["a"],
            "b": operacion["b"],
            "resultado": operacion["resultado"],
            "date": operacion["date"].isoformat(),
            "operacion": operacion["operacion"]
        })
    return {"historial": historial}


@app.post("/calculadora/batch")
def operaciones_en_batch(payload: List[dict] = Body(...)):
    """
    Recibe lista de operaciones:
    [
      {"op":"sum","nums":[2,4]},
      {"op":"mul","nums":[2,5]}
    ]
    """
    if not isinstance(payload, list) or len(payload) == 0:
        raise HTTPException(status_code=400, detail={"error": "Lista vacía o inválida"})

    out = []

    for item in payload:
        op = (item.get("op") or "").strip()
        nums = item.get("nums")

        if op not in {"sum", "sub", "mul", "div"}:
            raise HTTPException(status_code=400, detail={"error": f"Operación inválida: {op}"})
        if not isinstance(nums, list) or len(nums) < 2:
            raise HTTPException(status_code=400, detail={"error": "Cada operación requiere al menos 2 números"})

        
        if any(float(n) < 0 for n in nums):
            raise HTTPException(status_code=400, detail=_error_payload("No se permiten números negativos", op, nums))

        
        nums = list(map(float, nums))
        if op == "sum":
            res = sum(nums)
        elif op == "sub":
            res = nums[0]
            for n in nums[1:]:
                res -= n
        elif op == "mul":
            res = 1.0
            for n in nums:
                res *= n
        elif op == "div":
            if any(n == 0 for n in nums[1:]):
                raise HTTPException(status_code=403, detail=_error_payload("Division entre cero", "div", nums))
            res = nums[0]
            for n in nums[1:]:
                res /= n

        
        a_val = nums[0] if len(nums) >= 1 else 0.0
        b_val = nums[1] if len(nums) >= 2 else 0.0
        _guardar_historial(op, a_val, b_val, res)

        out.append({"op": op, "result": res})

    return out
