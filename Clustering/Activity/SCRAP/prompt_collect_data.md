I will give you a sentence that describes a global task.  
Your mission: generate a list of "task_items" that correspond exactly to this task.  

Rules:  
- Each "task_item" should be a short sentence describing a file, an application, a website, or a command used to accomplish this task.  
- For a file, include: name, extension/type, directory if relevant, application used to open it, and a concise description of what it does.  
- For an application, include: name and usage.  
- For a website, include: name, directory if relevant, application used to open it, and usage.  
- For a command, include only a concise description, without the prefix "Command".  
- The list of "task_items" should be varied, but it must include **at least 3 files and 3 commands**. It can also include applications and websites if relevant.  
- **Output only the task_items**: no explanations, no JSON wrapper, no extra text. Each sentence should be enclosed in quotes and separated by commas, like this:

"task_item 1",
"task_item 2",
"...",
"task_item N"

Here is the global task to process:  
"{global_task_description}"
