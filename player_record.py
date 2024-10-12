import os

def read_player_record(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist. Creating a new file with default content.")
        default_content = """
# Player Record

## Player Information
**Name:** Arjuna

## Alerts
_No alerts yet._

## Knowledge
- **Variables:** Not demonstrated
- **Loops:** Not demonstrated
- **Recursion:** Not demonstrated
"""
        with open(file_path, "w") as file:
            file.write(default_content)
        return default_content

    with open(file_path, "r") as file:
        return file.read()

def write_player_record(file_path, content):
    with open(file_path, "w") as file:
        file.write(content)

def format_player_record(player_info, alerts, knowledge):
    record = "# Player Record\n\n## Player Information\n"
    for key, value in player_info.items():
        record += f"**{key}:** {value}\n"
    
    record += "\n## Alerts\n"
    if alerts:
        for alert in alerts:
            record += f"- **{alert['date']}:** {alert['note']}\n"
    else:
        record += "_No alerts yet._\n"
    
    record += "\n## Knowledge\n"
    for key, value in knowledge.items():
        record += f"- **{key}:** {value}\n"
    
    return record

def parse_player_record(markdown_content):
    student_info = {}
    alerts = []
    knowledge = {}
    
    current_section = None
    lines = markdown_content.split("\n")
    
    for line in lines:
        line = line.strip()  # Strip leading/trailing whitespace
        if line.startswith("## "):
            current_section = line[3:].strip()
        elif current_section == "Player Information" and line.startswith("**"):
            if ":** " in line:
                key, value = line.split(":** ", 1)
                key = key.strip("**").strip()
                value = value.strip()
                student_info[key] = value
        elif current_section == "Alerts":
            if "_No alerts yet._" in line:
                alerts = []
            elif line.startswith("- **"):
                if ":** " in line:
                    date, note = line.split(":** ", 1)
                    date = date.strip("- **").strip()
                    note = note.strip()
                    alerts.append({"date": date, "note": note})
        elif current_section == "Knowledge" and line.startswith("- **"):
            if ":** " in line:
                key, value = line.split(":** ", 1)
                key = key.strip("- **").strip()
                value = value.strip()
                knowledge[key] = value
    
    final_record = {
        "Player Information": student_info,
        "Alerts": alerts,
        "Knowledge": knowledge
    }
    print(f"Final parsed record: {final_record}")
    return final_record

def save_player_character(character):
    file_path = "player_record.md"
    record = f"""
       ## Player character
       {character}
    """
    
    write_player_record(file_path, record)

def get_player_character():
    file_path = "player_record.md"
    return read_player_record(file_path)