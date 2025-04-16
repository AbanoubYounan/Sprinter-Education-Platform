import http.client
import json

def get_courses():
    # Define the API URL and the endpoint
    conn = http.client.HTTPSConnection("sprinter-back.mes-design.com")

    # Define the API path
    url = "/api/courses/lessons"

    # Send GET request to the API
    conn.request("GET", url)

    # Get the response from the server
    response = conn.getresponse()

    # Check if the response status is successful (200)
    if response.status == 200:
        # Read the response data
        data = response.read().decode()

        # Parse the JSON response
        data = json.loads(data)

        # Initialize a dictionary to store the courses in the desired format
        transformed_courses = {}

        # Loop through the courses in the response and transform them
        for course_title, course_data in data["courses"].items():
            # Extract the course description and lessons
            course_desc = course_data["course_disc"]
            lessons = {}

            # Loop through the lessons and create the desired lesson format
            for lesson_key, lesson_data in course_data["lessons"].items():
                lesson_title = lesson_data["lesson_title"]
                lesson_desc = lesson_data["lesson_disc"]
                lessons[lesson_key] = {
                    "lesson_title": lesson_title,
                    "lesson_disc": lesson_desc
                }

            # Add the course data to the transformed_courses dictionary
            transformed_courses[course_title.strip()] = {
                "course_disc": course_desc.strip(),
                "lessons": lessons
            }

        # Close the connection
        conn.close()

        # Return the transformed courses
        return transformed_courses
    else:
        print(f"Error: {response.status}")
        conn.close()
        return {}