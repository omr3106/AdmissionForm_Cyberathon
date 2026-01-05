from django.shortcuts import render, redirect
from django.contrib import messages
import firebase_admin
from firebase_admin import credentials, firestore
import os

# --- Firebase Setup ---
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
COLLECTION_NAME = "admissions"

# --- Your Logic Functions ---
def check_mail(email):
    if ("@" not in email) or ("." not in email):
        return False
    splitt = email.split(".")[-1]
    if splitt in ["com", 'in']:
        return True
    return False

def check_number(contact):
    if contact.startswith("+91") and contact[3:].isdigit() and len(contact) == 13:
        return True
    return False

# --- Views ---
def home(request):
    # Handle Submission
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        gender = request.POST.get('gender')
        stream = request.POST.get('stream')

        if not check_mail(email):
            messages.error(request, "Error: Invalid Email (.com or .in required)")
        elif not check_number(contact):
            messages.error(request, "Error: Invalid Contact (Start with +91, 13 digits)")
        elif not all([name, email, contact, gender, stream]):
            messages.error(request, "Error: All fields are required")
        else:
            # Save to Firebase
            data = {"Name": name, "Email": email, "Contact": contact, "Gender": gender, "Stream": stream}
            db.collection(COLLECTION_NAME).add(data)
            messages.success(request, "Student Registered Successfully!")
            return redirect('home')

    # Fetch Records for Display
    students = []
    try:
        docs = db.collection(COLLECTION_NAME).stream()
        for doc in docs:
            d = doc.to_dict()
            d['id'] = doc.id
            students.append(d)
    except Exception as e:
        messages.error(request, f"DB Error: {e}")

    return render(request, 'home.html', {'students': students})

def delete_record(request, doc_id):
    db.collection(COLLECTION_NAME).document(doc_id).delete()
    return redirect('home')

def edit_record(request, doc_id):
    # Simplified: We delete old and add new (or you can update)
    # For now, let's just use home to re-add. 
    # To keep it simple, I am skipping a separate Edit page.
    # Users usually delete and re-submit in simple apps.
    pass
def update_record(request, doc_id):
    # Reference the document
    doc_ref = db.collection(COLLECTION_NAME).document(doc_id)

    # 1. IF SUBMITTED (POST): Update the data
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        gender = request.POST.get('gender')
        stream = request.POST.get('stream')

        # Basic Validation (Same as home)
        if not check_mail(email) or not check_number(contact) or not name:
            messages.error(request, "Error: Invalid Input")
            return redirect('update', doc_id=doc_id) # Reload edit page if error

        updated_data = {
            "Name": name, "Email": email, "Contact": contact, 
            "Gender": gender, "Stream": stream
        }
        
        doc_ref.update(updated_data)
        messages.success(request, "Record Updated Successfully!")
        return redirect('home')

    # 2. IF LOADING PAGE (GET): Fetch existing data to fill the form
    doc = doc_ref.get()
    if not doc.exists:
        return redirect('home')
        
    student_data = doc.to_dict()
    student_data['id'] = doc.id
    
    return render(request, 'update.html', {'student': student_data})