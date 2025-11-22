"""
Sample Data Generator
Creates sample forms and responses for testing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
import random
import uuid

from database import (
    init_databases, get_dynamic_session,
    DynamicForm, DynamicFormField, DynamicFormResponse, DynamicResponseValue
)


def create_sample_forms():
    """Create sample forms with fields"""

    # Initialize databases
    init_databases()
    session = get_dynamic_session()

    try:
        # Sample Form 1: Customer Feedback
        feedback_form = DynamicForm(
            session_id=str(uuid.uuid4()),
            title="Customer Feedback Form",
            description="Collect customer feedback about our services",
            action="#",
            method="POST"
        )
        session.add(feedback_form)
        session.flush()

        feedback_fields = [
            {"field_id": "name", "label": "Full Name", "field_type": "text", "name": "name", "required": True},
            {"field_id": "email", "label": "Email Address", "field_type": "email", "name": "email", "required": True},
            {"field_id": "rating", "label": "Overall Rating", "field_type": "select", "name": "rating",
             "options": ["1 - Poor", "2 - Fair", "3 - Good", "4 - Very Good", "5 - Excellent"]},
            {"field_id": "category", "label": "Feedback Category", "field_type": "radio", "name": "category",
             "options": ["Product", "Service", "Support", "Website", "Other"]},
            {"field_id": "comments", "label": "Additional Comments", "field_type": "textarea", "name": "comments"},
            {"field_id": "recommend", "label": "Would you recommend us?", "field_type": "radio", "name": "recommend",
             "options": ["Yes", "No", "Maybe"]}
        ]

        for i, field in enumerate(feedback_fields):
            form_field = DynamicFormField(
                field_id=field["field_id"],
                form_id=feedback_form.id,
                label=field["label"],
                field_type=field["field_type"],
                name=field["name"],
                required=field.get("required", False),
                options=field.get("options"),
                field_order=i
            )
            session.add(form_field)

        # Sample Form 2: Event Registration
        event_form = DynamicForm(
            session_id=str(uuid.uuid4()),
            title="Event Registration",
            description="Register for our upcoming conference",
            action="#",
            method="POST"
        )
        session.add(event_form)
        session.flush()

        event_fields = [
            {"field_id": "fullname", "label": "Full Name", "field_type": "text", "name": "fullname", "required": True},
            {"field_id": "email", "label": "Email", "field_type": "email", "name": "email", "required": True},
            {"field_id": "phone", "label": "Phone Number", "field_type": "tel", "name": "phone"},
            {"field_id": "company", "label": "Company", "field_type": "text", "name": "company"},
            {"field_id": "ticket_type", "label": "Ticket Type", "field_type": "select", "name": "ticket_type",
             "options": ["Standard", "VIP", "Student"]},
            {"field_id": "dietary", "label": "Dietary Requirements", "field_type": "checkbox", "name": "dietary",
             "options": ["Vegetarian", "Vegan", "Gluten-Free", "None"]}
        ]

        for i, field in enumerate(event_fields):
            form_field = DynamicFormField(
                field_id=field["field_id"],
                form_id=event_form.id,
                label=field["label"],
                field_type=field["field_type"],
                name=field["name"],
                required=field.get("required", False),
                options=field.get("options"),
                field_order=i
            )
            session.add(form_field)

        # Sample Form 3: Contact Us
        contact_form = DynamicForm(
            session_id=str(uuid.uuid4()),
            title="Contact Us",
            description="Get in touch with our team",
            action="#",
            method="POST"
        )
        session.add(contact_form)
        session.flush()

        contact_fields = [
            {"field_id": "name", "label": "Your Name", "field_type": "text", "name": "name", "required": True},
            {"field_id": "email", "label": "Email", "field_type": "email", "name": "email", "required": True},
            {"field_id": "subject", "label": "Subject", "field_type": "select", "name": "subject",
             "options": ["General Inquiry", "Support", "Sales", "Partnership", "Other"]},
            {"field_id": "message", "label": "Message", "field_type": "textarea", "name": "message", "required": True}
        ]

        for i, field in enumerate(contact_fields):
            form_field = DynamicFormField(
                field_id=field["field_id"],
                form_id=contact_form.id,
                label=field["label"],
                field_type=field["field_type"],
                name=field["name"],
                required=field.get("required", False),
                options=field.get("options"),
                field_order=i
            )
            session.add(form_field)

        session.commit()

        print(f"Created forms:")
        print(f"  - Customer Feedback Form (ID: {feedback_form.session_id})")
        print(f"  - Event Registration (ID: {event_form.session_id})")
        print(f"  - Contact Us (ID: {contact_form.session_id})")

        return [feedback_form, event_form, contact_form]

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def create_sample_responses(forms):
    """Create sample responses for forms"""

    session = get_dynamic_session()

    # Sample data
    names = ["John Smith", "Jane Doe", "Bob Johnson", "Alice Williams", "Charlie Brown",
             "Diana Prince", "Edward Norton", "Fiona Apple", "George Lucas", "Helen Troy"]

    companies = ["Acme Corp", "TechStart", "GlobalTech", "InnovateCo", "DataDriven", "CloudFirst"]

    ratings = ["1 - Poor", "2 - Fair", "3 - Good", "4 - Very Good", "5 - Excellent"]
    categories = ["Product", "Service", "Support", "Website", "Other"]
    recommends = ["Yes", "No", "Maybe"]

    ticket_types = ["Standard", "VIP", "Student"]
    subjects = ["General Inquiry", "Support", "Sales", "Partnership", "Other"]

    comments = [
        "Great service, very satisfied!",
        "Could be better, had some issues.",
        "Excellent experience overall.",
        "Average service, nothing special.",
        "Very helpful support team!",
        "The website is easy to use.",
        "Product quality is outstanding.",
        "Fast delivery, good packaging.",
        "Would definitely recommend!",
        "Need improvement in customer service."
    ]

    try:
        feedback_form = forms[0]
        event_form = forms[1]
        contact_form = forms[2]

        # Create 20 feedback responses
        for i in range(20):
            response = DynamicFormResponse(
                form_id=feedback_form.id,
                submitted_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                ip_address=f"192.168.1.{random.randint(1, 255)}"
            )
            session.add(response)
            session.flush()

            name = random.choice(names)
            values = [
                ("name", name, "text"),
                ("email", f"{name.lower().replace(' ', '.')}@email.com", "email"),
                ("rating", random.choice(ratings), "select"),
                ("category", random.choice(categories), "radio"),
                ("comments", random.choice(comments), "textarea"),
                ("recommend", random.choice(recommends), "radio")
            ]

            for field_name, value, field_type in values:
                rv = DynamicResponseValue(
                    response_id=response.id,
                    field_name=field_name,
                    value=value,
                    field_type=field_type
                )
                session.add(rv)

        feedback_form.response_count = 20

        # Create 15 event registrations
        for i in range(15):
            response = DynamicFormResponse(
                form_id=event_form.id,
                submitted_at=datetime.utcnow() - timedelta(days=random.randint(0, 14)),
                ip_address=f"10.0.0.{random.randint(1, 255)}"
            )
            session.add(response)
            session.flush()

            name = random.choice(names)
            values = [
                ("fullname", name, "text"),
                ("email", f"{name.lower().replace(' ', '.')}@company.com", "email"),
                ("phone", f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}", "tel"),
                ("company", random.choice(companies), "text"),
                ("ticket_type", random.choice(ticket_types), "select"),
                ("dietary", random.choice(["Vegetarian", "Vegan", "None"]), "checkbox")
            ]

            for field_name, value, field_type in values:
                rv = DynamicResponseValue(
                    response_id=response.id,
                    field_name=field_name,
                    value=value,
                    field_type=field_type
                )
                session.add(rv)

        event_form.response_count = 15

        # Create 10 contact messages
        for i in range(10):
            response = DynamicFormResponse(
                form_id=contact_form.id,
                submitted_at=datetime.utcnow() - timedelta(days=random.randint(0, 7)),
                ip_address=f"172.16.0.{random.randint(1, 255)}"
            )
            session.add(response)
            session.flush()

            name = random.choice(names)
            values = [
                ("name", name, "text"),
                ("email", f"{name.lower().replace(' ', '_')}@gmail.com", "email"),
                ("subject", random.choice(subjects), "select"),
                ("message", random.choice(comments), "textarea")
            ]

            for field_name, value, field_type in values:
                rv = DynamicResponseValue(
                    response_id=response.id,
                    field_name=field_name,
                    value=value,
                    field_type=field_type
                )
                session.add(rv)

        contact_form.response_count = 10

        session.commit()

        print(f"\nCreated responses:")
        print(f"  - Customer Feedback: 20 responses")
        print(f"  - Event Registration: 15 responses")
        print(f"  - Contact Us: 10 responses")
        print(f"  - Total: 45 responses")

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def main():
    """Main function to create all sample data"""
    print("=" * 50)
    print("CREATING SAMPLE DATA")
    print("=" * 50)

    # Create forms
    forms = create_sample_forms()

    # Create responses
    create_sample_responses(forms)

    print("\n" + "=" * 50)
    print("SAMPLE DATA CREATED SUCCESSFULLY")
    print("=" * 50)

    return forms


if __name__ == "__main__":
    main()
