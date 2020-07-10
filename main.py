import json
from datetime import datetime, timedelta
import os


def find_folder():
    for r, d, f in os.walk(os.getcwd()):
        for dir in d:
            if "mydata" in dir:
                return dir
        print("Snapchat folder not found! Please add the folder to the directory and try again!")
        return ""


def interaction_history(folder, username, file, inter_type):
    with open(folder + "/json/" + file, "r") as f:
        chat_data = json.load(f)
        # used to populate output_data (ugliest line ever)
        now = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " UTC", '%Y-%m-%d %H:%M:%S %Z')
        output_data = {
            "received": {
                "total_with_un": 0,
                "date_min": now,
                "date_max": now - timedelta(20),  # idea is to have a date that will be reasonably overwritten,
                "overall_total": len(chat_data[f"Received {inter_type.capitalize()} History"])
            },
            "sent": {
                "total_with_un": 0,
                "date_min": now,
                "date_max": now - timedelta(20),
                "overall_total": len(chat_data[f"Sent {inter_type.capitalize()} History"])
            }
        }

        def parse_inter(type, flag, data_loc):
            for chat in chat_data[type]:
                if chat[flag] == username:

                    output_data[data_loc]["total_with_un"] += 1
                curr_date = datetime.strptime(chat["Created"], '%Y-%m-%d %H:%M:%S %Z')
                if curr_date < output_data[data_loc]["date_min"]:
                    output_data[data_loc]["date_min"] = curr_date
                elif curr_date > output_data[data_loc]["date_max"]:
                    output_data[data_loc]["date_max"] = curr_date

        parse_inter(f"Received {inter_type.capitalize()} History", "From", "received")
        parse_inter(f"Sent {inter_type.capitalize()} History", "To", "sent")

        # concise, readable workaround from creating variables?
        abs_min_date = min(output_data["sent"]["date_min"], output_data["received"]["date_min"])
        abs_max_date = max(output_data["sent"]["date_max"], output_data["received"]["date_max"])
        duration_days = round((abs_max_date - abs_min_date).total_seconds()/60/60/24, 2)

        print(f"""
{inter_type.capitalize()} interactions with {username}:
    From: {abs_min_date.strftime("%A, %B %d %Y")} - {abs_max_date.strftime("%A, %B %d %Y")}
        Duration: {duration_days} days
    Total snaps sent: {output_data["sent"]["total_with_un"]}
        Percentage: {round(output_data["sent"]["total_with_un"]/output_data["sent"]["overall_total"], 2) * 100}%
        Fraction: {output_data["sent"]["total_with_un"]}/{output_data["sent"]["overall_total"]}
            Difference: {output_data["sent"]["overall_total"] - output_data["sent"]["total_with_un"]} snaps with other users
        Snaps/Day: {round(output_data["sent"]["total_with_un"]/duration_days, 2)} snaps/day
    Total snaps received: {output_data["received"]["total_with_un"]}    
        Percentage: {round(output_data["received"]["total_with_un"]/output_data["received"]["overall_total"], 2) * 100}%
        Fraction: {output_data["received"]["total_with_un"]}/{output_data["received"]["overall_total"]}
            Difference: {output_data["received"]["overall_total"] - output_data["received"]["total_with_un"]} snaps with other users
        Snaps/Day: {round(output_data["received"]["total_with_un"]/duration_days, 2)} snaps/day

""")


def most_snapped(folder, files, inter_types, top_num):
    snap_list = {"rec": {}, "sent": {}}
    for file, inter_type in zip(files, inter_types):
        with open(folder + "/json/" + file, "r") as f:
            data = json.load(f)

            def parse_inter(type, flag, data_loc):
                for chat in data[type]:
                    media_type = chat["Media Type"]
                    if chat["Media Type"] == "":
                        media_type = "NULL"
                    # if username is in dictionary
                    if chat[flag] in snap_list[data_loc]:
                        # if media type is in the user's dict
                        if media_type in snap_list[data_loc][chat[flag]]:
                            snap_list[data_loc][chat[flag]][media_type] += 1
                        else:
                            snap_list[data_loc][chat[flag]][media_type] = 1
                    else:
                        snap_list[data_loc][chat[flag]] = {}
                        snap_list[data_loc][chat[flag]][media_type] = 1

            parse_inter(f"Received {inter_type.capitalize()} History", "From", "rec")
            parse_inter(f"Sent {inter_type.capitalize()} History", "To", "sent")

            # probably redundant in some sense
            ordered_snaps = {}
            for key in snap_list.keys():
                ordered_snaps[key] = {}
                for key2 in snap_list[key].keys():
                    ordered_snaps[key][key2] = sum(snap_list[key][key2].values())

            for key in ordered_snaps.keys():
                ordered_snaps[key] = sorted(ordered_snaps[key].items(), key=lambda item: item[1], reverse=True)

    def output_data(data_source):
        for un in ordered_snaps[data_source][:top_num]:
            # a string breakdown of the types of snaps sent
            breakdown_output = ""
            for key, value in snap_list[data_source][un[0]].items():
                breakdown_output += f"{key.capitalize()}: {value} / "
            print(f"{un[0]}: {un[1]} ({breakdown_output[:-3]})")

    print("Received Messages Ranking:\n--------\n")
    output_data("rec")
    print("\n\nSent Messages Ranking:\n--------\n")
    output_data("sent")


def user_selection(folder):
    print("""
0. Exit
1. See interaction with a specific user/group
2. See information with your most snapped users/groups
    """)
    selection = ""
    while not isinstance(selection, int):
        selection = input("What do you want to do? (Enter the corresponding number)")
        try:
            selection = int(selection)
        except ValueError:
            print("Please enter a number!")
        if isinstance(selection, int):
            if selection < 0 or selection > 2:
                print("Please enter a valid number!")
                selection = ""
    if selection == 0:
        return 0
    elif selection == 1:
        username = str(input("Enter a valid Snapchat username/groupname to see the available data: "))
        interaction_history(folder, username, "chat_history.json", "chat")
        interaction_history(folder, username, "snap_history.json", "snap")
        return 1
    elif selection == 2:
        top_num = ""
        while not isinstance(top_num, int):
            top_num = input("How many users/groups do you want to display? (10 or under, but above 0)")
            try:
                top_num = int(top_num)
            except ValueError:
                print("Please enter a number!")
            if isinstance(top_num, int):
                if top_num <= 0 or top_num > 10:
                    print("Please enter a valid number!")
                    top_num = ""
        most_snapped(folder, ["chat_history.json", "snap_history.json"], ["chat", "snap"], top_num)
        return 1


def main():
    folder = find_folder()
    if folder == "":
        return
    print("""

Welcome to the unofficial Snapchat data analyzer!
Get detailed information about snaps with specific user/group, your most snapped users/groups, and more!

Created by Carter
--------""")
    while True:
        if user_selection(folder) == 0:
            print("Bye!")
            break


main()
