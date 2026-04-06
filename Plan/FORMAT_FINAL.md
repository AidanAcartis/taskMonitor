```json
{
  "clusters": [
    {
      "cluster_id": "2",
      "global_task_intention": "Create a code file",
      "cohesion": 0.436,

      "stats": {
        "total_duration": 0.24,
        "num_events": 2,
        "start": "2026-04-06 10:46:46",
        "end": "2026-04-06 10:47:30"
      },

      "task_items": [
        {
          "description": "visual studio code, code editor, used by the user",
          "total_duration": 0.07,
          "occurrences": 1
        },
        {
          "description": "documents, directory, navigated by the user",
          "total_duration": 0.17,
          "occurrences": 1
        }
      ],

      "events": [
        {
          "event_id": 12,
          "date": "2026-04-06",
          "start": "10:47:28",
          "end": "10:47:30",
          "duration": 0.07,
          "event_type": "app",
          "file": "",
          "app": "Visual Studio Code",
          "command": "",
          "raw": "Visual Studio Code",
          "description": "visual studio code, code editor, used by the user"
        },
        {
          "event_id": 7,
          "date": "2026-04-06",
          "start": "10:46:46",
          "end": "10:46:56",
          "duration": 0.17,
          "event_type": "directory",
          "file": "",
          "app": "",
          "command": "",
          "raw": "Documents",
          "description": "documents, directory, navigated by the user"
        }
      ]
    }
  ]
}
```