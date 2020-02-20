from datetime import datetime, timezone
from gqlpycgen.api import ISO_FORMAT


def wf_strptime(date_string):
    return datetime.strptime(date_string, ISO_FORMAT).replace(tzinfo=timezone.utc)


def get_environment_id(honeycomb_client, environment_name):
    environments = honeycomb_client.query.findEnvironment(name=environment_name)
    return environments.data[0].get('environment_id')


def fetch_inference_for_inference_id(honeycomb_client, inference_id):
    return honeycomb_client.query.query(
        """
        query getInferenceForInferenceId ($inference_id: ID!) {
          getInferenceExecution(inference_id: $inference_id) {
            inference_id
            inference_name: name
            inference_model: model
            inference_version: version
          }
        }
        """,
        {"inference_id": inference_id}).get('getInferenceExecution')


def fetch_first_pose_for_inference_id(honeycomb_client, inference_id):
    data = honeycomb_client.query.query(
        """
        query getFirstPoseFromInferenceId ($inference_id: String!) {
          searchPoses2D (
            query: {
              field: "source",
              operator: EQ,
              value: $inference_id
            }
            page: { max: 1}
          ) {
            poses: data {
              time: timestamp
              camera {
                device_id
                device_name: name
                assignments {
                  assignment_id
                  environment {
                    environment_id
                    environment_name: name
                  }
                  start
                  end
                }
              }
            }
          }
        }
        """,
        {"inference_id": inference_id})
    return next((p for p in data.get('searchPoses2D').get('poses')), None)


def fetch_assignments(honeycomb_client, environment_id):
    return honeycomb_client.query.query(
        """
        query getEnvironment ($environment_id: ID!) {
          getEnvironment(environment_id: $environment_id) {
            environment_id
            name
            assignments {
              assignment_id
              start
              end
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


def filter_assignments_at_time(assignments, time):
    return list(filter(lambda a: (
            wf_strptime(a['start']) <= time and
            (a['end'] is None or wf_strptime(a['end']) >= time)
    ), assignments))


def get_environment_for_inference_id(honeycomb_client, inference_id):
    pose = fetch_first_pose_for_inference_id(honeycomb_client, inference_id)
    if pose is None:
        return None

    assignment = next(iter(filter_assignments_at_time(pose.get('camera').get('assignments'), wf_strptime(pose['time']))), dict())
    environment = assignment.get('environment', dict())

    return {
        'environment_id': environment.get('environment_id', None),
        'environment_name': environment.get('environment_name', None)
    }


def get_assignments_at_time(honeycomb_client, environment_id, time):
    assignments = fetch_assignments(honeycomb_client, environment_id)
    filtered_assignments = filter_assignments_at_time(assignments, time)
    return [(assignment["assignment_id"], assignment["assigned"]["name"]) for assignment in filtered_assignments if "name" in assignment["assigned"] and assignment["assigned"]["name"].startswith("cc")]


def get_device_to_assignment_mapping_at_time(honeycomb_client, environment_id, time):
    assignments = fetch_assignments(honeycomb_client, environment_id)
    filtered_assignments = filter_assignments_at_time(assignments, time)
    return {assignment["assigned"]["device_id"]: assignment["assignment_id"] for assignment in filtered_assignments if "name" in assignment["assigned"] and assignment["assigned"]["name"].startswith("cc")}

