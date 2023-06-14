import os


def delete_directory(directory):
    # Iterate over all files and directories in the given directory
    for filename in os.listdir(directory):
        file_path = directory + "/" + filename
        # Check if the current item is a file
        if file_path != "./lib":
            try:
                # Remove the file
                os.remove(file_path)
                print(f"removed: {file_path}")
            except:
                # Recursively delete the subdirectory
                delete_directory(file_path)

        else:
            print(f"skipping: {file_path}")


delete_directory(".")
