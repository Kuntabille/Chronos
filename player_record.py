import os



def write_player_record(file_path, content):
    with open(file_path, "w") as file:
        file.write(content)


def save_player_character(character):
    file_path = "player_record.md"
    record = f"""
       ## Player character
       {character}
    """
    
    write_player_record(file_path, record)