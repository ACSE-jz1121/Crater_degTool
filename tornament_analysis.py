import tkinter as tk
from PIL import Image, ImageTk
import os
from glob import glob
import random

# Load all crater images from the specified folder and convert paths to absolute
image_folder = "100_images\extracted_images"
crater_images = [os.path.abspath(path) for path in glob(os.path.join(image_folder, "*.jpg"))]
print('Crater images list:', crater_images)

# Paths to demonstration images for degradation levels 1 to 4
demo_image_paths = [
    os.path.abspath(r"C:/Users/jamil/OneDrive/desktop/PhD/Phase_2/gui/classification/demonstration_img/1.jpg"),
    os.path.abspath(r"C:/Users/jamil/OneDrive/desktop/PhD/Phase_2/gui/classification/demonstration_img/2.jpg"),
    os.path.abspath(r"C:/Users/jamil/OneDrive/desktop/PhD/Phase_2/gui/classification/demonstration_img/3.jpg"),
    os.path.abspath(r"C:/Users/jamil/OneDrive/desktop/PhD\Phase_2\gui\classification\demonstration_img\4.jpg")
]

# Global variables for the main window, image labels, and counters
window = tk.Tk()
window.title("Crater Comparison")
button_press_count = 0  # Counter to track the number of button presses

# Variables for comparison history
comparison_history = []  # List of dictionaries with comparison details
current_comparison_index = -1  # Index in the comparison history

# Function to load existing data from a file
def load_existing_data(file_path):
    existing_scores = {image: 0 for image in crater_images}
    existing_counts = {image: 0 for image in crater_images}
    existing_wins = {image: 0 for image in crater_images}
    existing_losses = {image: 0 for image in crater_images}
    existing_draws = {image: 0 for image in crater_images}
    total_button_presses = 0

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            for line in file:
                try:
                    if line.startswith("Total Button Presses:"):
                        total_button_presses = int(line.strip().split(": ")[1])
                    elif " - Score: " in line and " - Samples: " in line:
                        parts = line.strip().split(" - Score: ")
                        image_name = parts[0]
                        score_samples = parts[1].split(" - Samples: ")
                        score = score_samples[0].strip()
                        samples_wins = score_samples[1].strip().split(" - Wins: ")
                        samples = samples_wins[0].strip()
                        wins_losses_draws = samples_wins[1].split(" - Losses: ")
                        wins = wins_losses_draws[0].strip()
                        losses_draws = wins_losses_draws[1].split(" - Draws: ")
                        losses = losses_draws[0].strip()
                        draws = losses_draws[1].strip()

                        for image_path in crater_images:
                            if os.path.basename(image_path) == image_name:
                                existing_scores[image_path] = int(score)
                                existing_counts[image_path] = int(samples)
                                existing_wins[image_path] = int(wins)
                                existing_losses[image_path] = int(losses)
                                existing_draws[image_path] = int(draws)
                    else:
                        continue
                except ValueError as e:
                    # Print out the problematic line for debugging
                    print(f"Error parsing line: {line}")
                    print(f"Error: {e}")
                    continue  # Skip the problematic line and continue processing
    return existing_scores, existing_counts, existing_wins, existing_losses, existing_draws, total_button_presses

# Load existing data at the start
file_path = os.path.join(image_folder, "results", "sorted_crater_images.txt")
existing_scores, existing_counts, existing_wins, existing_losses, existing_draws, total_button_presses = load_existing_data(file_path)

# Initialize points dictionary to track scores, wins, losses, draws, and counts for each image
image_scores = existing_scores.copy()
image_counts = existing_counts.copy()
image_wins = existing_wins.copy()
image_losses = existing_losses.copy()
image_draws = existing_draws.copy()
button_press_count = total_button_presses  # Continue from the last button press count

# Function to initialize the main comparison window
def initialize_interface():
    # Configure grid to evenly distribute space
    window.columnconfigure([0, 1, 2, 3], weight=1)
    window.rowconfigure([0, 1], weight=1, minsize=100)
    
    # Load and display demonstration images with degradation levels
    for i, path in enumerate(demo_image_paths):
        demo_image = ImageTk.PhotoImage(Image.open(path).resize((100, 100)))
        demo_label = tk.Label(window, image=demo_image)
        demo_label.grid(row=0, column=i, padx=10, pady=10)
        label_text = tk.Label(window, text=f"Level {i + 1}")
        label_text.grid(row=1, column=i, padx=10, pady=5)
        demo_label.image = demo_image  # Keep a reference to avoid garbage collection

    # Create labels for the comparison images
    global label1, label2, btn1, btn2, btn_same, btn_last_page, btn_next_page
    label1 = tk.Label(window)
    label1.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky='e')
    label2 = tk.Label(window)
    label2.grid(row=2, column=2, columnspan=2, padx=20, pady=10, sticky='w')

    # Create buttons for selecting which image is more degraded or if both are similar
    btn1 = tk.Button(window, text="Left is More Degraded", command=lambda: select_image(True))
    btn1.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky='e')
    btn2 = tk.Button(window, text="Right is More Degraded", command=lambda: select_image(False))
    btn2.grid(row=3, column=2, columnspan=2, padx=10, pady=10, sticky='w')
    
    # Add a button for "Both are Similarly Degraded"
    btn_same = tk.Button(window, text="Both are Similarly Degraded", command=lambda: select_image(None))
    btn_same.grid(row=4, column=1, columnspan=2, padx=10, pady=10)

    # Reposition "Last Page" button to the same row as "Both are Similarly Degraded", at the very left side
    btn_last_page = tk.Button(window, text="Last Page", command=last_page)
    btn_last_page.grid(row=4, column=0, padx=10, pady=10, sticky='w')

    # Add "Next Page" button to the same row, at the very right side
    btn_next_page = tk.Button(window, text="Next Page", command=next_page)
    btn_next_page.grid(row=4, column=3, padx=10, pady=10, sticky='e')

    # Start the first comparison
    next_page()
    
    # Save data when the window is closed
    def on_closing():
        save_sorted_sequence()  # Save the data before exiting
        window.destroy()  # Close the window

    window.protocol("WM_DELETE_WINDOW", on_closing)  # Trigger the on_closing function when the window is closed

# Function to update the images for comparison
def update_comparison():
    global current_left_image, current_right_image

    # Get the current comparison from the history
    current_comparison = comparison_history[current_comparison_index]
    current_left_image = os.path.abspath(current_comparison['img1'])
    current_right_image = os.path.abspath(current_comparison['img2'])

    # Load and display images
    image1 = ImageTk.PhotoImage(Image.open(current_left_image).resize((200, 200)))
    image2 = ImageTk.PhotoImage(Image.open(current_right_image).resize((200, 200)))
    label1.config(image=image1)
    label2.config(image=image2)
    label1.image = image1  # Keep a reference to avoid garbage collection
    label2.image = image2  # Keep a reference to avoid garbage collection

    # Update button states
    update_navigation_buttons()

# Function to handle the user's decision and proceed
def select_image(is_left_more_degraded):
    global image_scores, image_counts, image_wins, image_losses, image_draws, button_press_count

    # Retrieve the current comparison
    current_comparison = comparison_history[current_comparison_index]

    # If a previous choice exists, undo its impact on the scores
    previous_choice = current_comparison.get('choice')
    if previous_choice is not None:
        undo_previous_choice(current_comparison)

    # Record the new choice
    current_comparison['choice'] = is_left_more_degraded

    # Update scores based on user selection
    if is_left_more_degraded is True:
        image_scores[current_left_image] += 2  # Add 2 points to the left image for winning
        image_wins[current_left_image] += 1  # Increment win for left image
        image_losses[current_right_image] += 1  # Increment loss for right image
    elif is_left_more_degraded is False:
        image_scores[current_right_image] += 2  # Add 2 points to the right image for winning
        image_wins[current_right_image] += 1  # Increment win for right image
        image_losses[current_left_image] += 1  # Increment loss for left image
    else:
        # If both are similarly degraded, update draws for both images and give each 1 point
        image_draws[current_left_image] += 1
        image_draws[current_right_image] += 1
        image_scores[current_left_image] += 1  # Both get 1 point for a draw
        image_scores[current_right_image] += 1

    # Update sample counts for both images involved in the comparison
    image_counts[current_left_image] += 1
    image_counts[current_right_image] += 1

    button_press_count += 1  # Increment the button press counter

    print(f'Scores updated: {current_left_image}: {image_scores[current_left_image]}, {current_right_image}: {image_scores[current_right_image]}')
    print(f'Wins/Losses/Draws updated: {current_left_image}: {image_wins[current_left_image]}/{image_losses[current_left_image]}/{image_draws[current_left_image]}, {current_right_image}: {image_wins[current_right_image]}/{image_losses[current_right_image]}/{image_draws[current_right_image]}')
    print(f'Sample counts updated: {current_left_image}: {image_counts[current_left_image]}, {current_right_image}: {image_counts[current_right_image]}')
    print(f'Button pressed {button_press_count} times.')

    # Save results immediately after each button press
    save_sorted_sequence()

    # Proceed to the next comparison
    next_page()

# Function to undo the previous choice when re-evaluating a comparison
def undo_previous_choice(comparison):
    global image_scores, image_counts, image_wins, image_losses, image_draws

    img1 = comparison['img1']
    img2 = comparison['img2']
    choice = comparison['choice']

    # Reverse the previous updates
    if choice is True:
        image_scores[img1] -= 2
        image_wins[img1] -= 1
        image_losses[img2] -= 1
    elif choice is False:
        image_scores[img2] -= 2
        image_wins[img2] -= 1
        image_losses[img1] -= 1
    else:
        image_scores[img1] -= 1
        image_scores[img2] -= 1
        image_draws[img1] -= 1
        image_draws[img2] -= 1

    # Decrement sample counts
    image_counts[img1] -= 1
    image_counts[img2] -= 1

    # Decrement the button press count
    global button_press_count
    button_press_count -= 1

# Function to show the next comparison
def next_page():
    global current_comparison_index, comparison_history
    current_comparison_index += 1

    if current_comparison_index < len(comparison_history):
        # Existing comparison in history
        update_comparison()
    else:
        # Generate a new random comparison and add it to the history
        img1, img2 = random.sample(crater_images, 2)
        comparison_history.append({
            'img1': img1,
            'img2': img2,
            'choice': None  # No choice made yet
        })
        update_comparison()

# Function to show the previous comparison
def last_page():
    global current_comparison_index
    if current_comparison_index > 0:
        current_comparison_index -= 1
        update_comparison()

def update_navigation_buttons():
    # Disable 'Last Page' button if at the first comparison
    if current_comparison_index <= 0:
        btn_last_page.config(state=tk.DISABLED)
    else:
        btn_last_page.config(state=tk.NORMAL)

    # Disable 'Next Page' button if at the last comparison with no choice made
    if current_comparison_index >= len(comparison_history) - 1 and comparison_history[current_comparison_index].get('choice') is None:
        btn_next_page.config(state=tk.DISABLED)
    else:
        btn_next_page.config(state=tk.NORMAL)

# Function to save the sorted sequence of craters with their scores
def save_sorted_sequence():
    try:
        # Define the file path to save the sorted sequence
        output_folder = os.path.join(image_folder, "results")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"Created directory: {output_folder}")

        file_path = os.path.join(output_folder, "sorted_crater_images.txt")

        # Sort images by their updated score in descending order
        sorted_images = sorted(image_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Write the updated scores, counts, wins, losses, draws, and total button presses back to the file
        with open(file_path, "w") as file:
            file.write(f"Total Button Presses: {button_press_count}\n\n")
            for image_path, score in sorted_images:
                # Extract and write the image name, updated score, sample count, wins, losses, and draws to the file
                file.write(f"{os.path.basename(image_path)} - Score: {score} - Samples: {image_counts[image_path]} - Wins: {image_wins[image_path]} - Losses: {image_losses[image_path]} - Draws: {image_draws[image_path]}\n")
        
        # Confirm that the results are saved
        print(f"Sorted sequence saved to {file_path}")
    except Exception as e:
        print(f"Error saving the sorted sequence: {e}")

# Initialize the interface and start the application
initialize_interface()
window.mainloop()
