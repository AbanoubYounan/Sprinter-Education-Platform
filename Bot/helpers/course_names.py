import http.client
import json

def get_course_titles():
    # Define the endpoint URL
    conn = http.client.HTTPSConnection("sprinter-back.mes-design.com")

    # Define the API path
    url = "/api/courses/names"

    # Send the GET request
    conn.request("GET", url)

    # Get the response
    response = conn.getresponse()

    # Check if the request was successful
    if response.status == 200:
        data = json.loads(response.read().decode())  # Parse the JSON response
        # Extract course titles
        course_titles = [course["course_title"] for course in data["courses"]]
        # Close the connection
        conn.close()
        return course_titles  # Return the course titles
    else:
        print(f"Error: {response.status}")
        # Close the connection
        conn.close()
        return []  # Return an empty list if the request failed

    

# Call the function and print the result
course_titles = get_course_titles()
print(course_titles)
