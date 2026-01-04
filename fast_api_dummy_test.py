from fastapi import FastAPI , Path , HTTPException, Query
import json
app = FastAPI()


def get_data():
    try:
        with open("patients.json", "r") as f:
            data = json.loads(f.read())
            return data
    except Exception as e:
        raise FileNotFoundError("File is corrupted or not found")

@app.get("/patients")
def get_patients():
    data = get_data()
    if data:
        return {"message": "success", "data": data}
    else:
        return HTTPException(500, "Internal Server Error")
    
@app.get("/patients/{patient_id}")
def get_patient_by_id(patient_id:str = Path(..., description="Patient Id in the database", example="P0001")):
    data = get_data()
    print(data)
    if patient_id in data:
        return data[patient_id]
    else:
        return HTTPException(404, f"Patient not found")
    

@app.get("/get_patients")
def get_query_patients(sort_by:str = Query(..., description="Send the value on the basis of sort will happen"), order_by: str = Query(default="asc", description="Order by 'asc' or 'desc'")):
    sorted_fields = ['age', "height"]
    if sort_by not in sorted_fields:
        return HTTPException(400, f"sorted_by should be from these: {sorted_fields}")
    
    if order_by not in ['desc', 'asc']:
        return HTTPException(400, f"order_by should be in {['desc', 'asc']}")
    order_by = True if order_by=="desc" else False
    
    data = get_data()
    try:
        sorted_data = sorted(data.values(), key = lambda x : x.get(sort_by, 0), reverse = order_by)
        return {"message": "success", "data": sorted_data}
    except Exception as e:
        raise e