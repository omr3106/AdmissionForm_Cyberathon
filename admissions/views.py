from django.shortcuts import render, redirect
from django.contrib import messages
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# --- Firebase Setup (Cloud & Local Compatible) ---
if not firebase_admin._apps:
    # 1. Check for Environment Variable (for Vercel/Render Deployment)
    if 'FIREBASE_KEY' in os.environ:
        # Load the key from the secured environment variable
        key_dict = json.loads(os.environ['FIREBASE_KEY'])
        cred = credentials.Certificate(key_dict)
    
    # 2. Fallback to Local File (for running on your laptop)
    else:
        # Ensure serviceAccountKey.json is in the root folder
        cred = credentials.Certificate("serviceAccountKey.json")

    firebase_admin.initialize_app(cred)

db = firestore.client()
COLLECTION_NAME = "admissions"

# --- Helper Functions for Validation ---
def check_mail(email):
    """Validates if email ends with .com or .in"""
    if ("@" not in email) or ("." not in email):
        return False
    splitt = email.split(".")[-1]
    if splitt in ["com", 'in']:
        return True
    return False

def check_number(contact):
    """Validates if contact starts with +91 and has 13 characters"""
    if contact.startswith("+91") and contact[3:].isdigit() and len(contact) == 13:
        return True
    return False

# --- Main Views ---

def home(request):
    """Handles the Home Page: Registration Form & Displaying Records"""
    
    # 1. Handle Form Submission (Create)
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        gender = request.POST.get('gender')
        stream = request.POST.get('stream')

        # Validation Logic
        if not check_mail(email):
            messages.error(request, "Error: Invalid Email (Must end with .com or .in)")
        elif not check_number(contact):
            messages.error(request, "Error: Invalid Contact (Must start with +91 and be 13 digits)")
        elif not all([name, email, contact, gender, stream]):
            messages.error(request, "Error: All fields are required")
        else:
            # Save to Firebase
            try:
                data = {
                    "Name": name, 
                    "Email": email, 
                    "Contact": contact, 
                    "Gender": gender, 
                    "Stream": stream
                }
                db.collection(COLLECTION_NAME).add(data)
                messages.success(request, "Student Registered Successfully!")
                return redirect('home')
            except Exception as e:
                messages.error(request, f"Database Error: {e}")

    # 2. Fetch Records for Display (Read)
    students = []
    try:
        docs = db.collection(COLLECTION_NAME).stream()
        for doc in docs:
            student_data = doc.to_dict()
            student_data['id'] = doc.id  # Attach ID for Edit/Delete actions
            students.append(student_data)
    except Exception as e:
        messages.error(request, f"Error fetching data: {e}")

    return render(request, 'home.html', {'students': students})

def update_record(request, doc_id):
    """Handles the Update Page: Fetch existing data & Save changes"""
    
    doc_ref = db.collection(COLLECTION_NAME).document(doc_id)

    # 1. If Form Submitted (POST) -> Update Data
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        gender = request.POST.get('gender')
        stream = request.POST.get('stream')

        # Validate again before updating
        if not check_mail(email):
            messages.error(request, "Error: Invalid Email")
            # We redirect back to the update page so they can fix it
            return redirect('update', doc_id=doc_id) 
        
        if not check_number(contact):
            messages.error(request, "Error: Invalid Contact")
            return redirect('update', doc_id=doc_id)

        try:
            updated_data = {
                "Name": name, 
                "Email": email, 
                "Contact": contact, 
                "Gender": gender, 
                "Stream": stream
            }
            doc_ref.update(updated_data)
            messages.success(request, "Record Updated Successfully!")
            return redirect('home')
        except Exception as e:
            messages.error(request, f"Update Error: {e}")

    # 2. If Loading Page (GET) -> Fetch Existing Data to Fill Form
    try:
        doc = doc_ref.get()
        if not doc.exists:
            messages.error(request, "Document not found!")
            return redirect('home')
            
        student_data = doc.to_dict()
        student_data['id'] = doc.id
        return render(request, 'update.html', {'student': student_data})
        
    except Exception as e:
        messages.error(request, f"Error loading document: {e}")
        return redirect('home')

def delete_record(request, doc_id):
    """Handles Deletion of a Record"""
    try:
        db.collection(COLLECTION_NAME).document(doc_id).delete()
        messages.success(request, "Record Deleted Successfully!")
    except Exception as e:
        messages.error(request, f"Deletion Error: {e}")
    
    return redirect('home')