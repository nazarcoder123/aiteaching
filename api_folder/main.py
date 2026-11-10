from fastapi import FastAPI # This lib is used to import the fastapi

app = FastAPI() # Here we are storing fastapi in app variable

students = [
    {"id": 1, "name": "Rahul"},
    {"id": 2, "name": "Amit"}
]

@app.get("/") # create an api end point [@ python decorator , app fastapi application object , "/" URL path of the end point]
def home():
    return {
        "message": "Welcome to fastapi"
    }


####---- We have covered CRUD [Create(post),Read(get),update(patch&update),delete] operations in python or REST API's ####----

# 1. GET - Read data
@app.get("/students") 
def get_students():
    return students

# 2. POST - Create data
@app.post("/students")
def create_students(student: dict):
    students.append(student)
    return {"message": "student added", "data": student}

# 3. PUT - Update data 
@app.put("/student/{id}")
def update_student(id:int,student: dict):
    for s in students:
        if s["id"] == id:
            s.update(student)
            return {"message": "student partially updated"}
    return {"message": "student not found"}


# 4. PATCH - Partial update 
@app.patch("/students/{id}")
def patch_student(id:int, data: dict):
    for s in students:
        if s["id"] == id:
            s.update(data)
            return {"message": "student partially updated"} 
    return {"message": "student not found"} 

# 5. DELETE - Delete data 
@app.delete("/students/{id}")
def delete_student(id:int):
    for s in students:
        if s["id"] == id:
            students.remove(s) 
            return {"message": "student deleted"} 
    return {"message": "student not found"}