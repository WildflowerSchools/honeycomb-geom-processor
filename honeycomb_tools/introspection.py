def get_environment_id(honeycomb_client, environment_name):
    environments = honeycomb_client.query.findEnvironment(name=environment_name)
    return environments.data[0].get('environment_id')


def fetch_assignments(honeycomb_client, environment_id):
    return honeycomb_client.query.query(
        """
        query getEnvironment ($environment_id: ID!) {
          getEnvironment(environment_id: $environment_id) {
            environment_id
            name
            assignments(current: true) {
              assignment_id
              assigned {
                ... on Device {
                  device_id
                  part_number
                  name
                  tag_id
                  description
                  serial_number
                  mac_address
                }
              }
            }
          }
        }
        """,
        {"environment_id": environment_id}).get("getEnvironment").get("assignments")


def get_assignments(honeycomb_client, environment_id):
    assignments = fetch_assignments(honeycomb_client, environment_id)
    return [(assignment["assignment_id"], assignment["assigned"]["name"]) for assignment in assignments if "name" in assignment["assigned"] and assignment["assigned"]["name"].startswith("cc")]


def get_device_to_assignment_mapping(honeycomb_client, environment_id):
    assignments = fetch_assignments(honeycomb_client, environment_id)
    return {assignment["assigned"]["device_id"]: assignment["assignment_id"] for assignment in assignments if "name" in assignment["assigned"] and assignment["assigned"]["name"].startswith("cc")}
