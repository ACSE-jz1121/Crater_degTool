import tkinter as tk
from PIL import Image, ImageTk
import os
from glob import glob
import random
import matplotlib
matplotlib.use("TkAgg")  # Use TkAgg backend for matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.stats import spearmanr

# Load all crater images from the specified folder and convert paths to absolute
image_folder = "600_images"
crater_images = [os.path.abspath(path) for path in glob(os.path.join(image_folder, "*.jpg"))]
print('Crater images list loaded. Total images:', len(crater_images))

# Paths to demonstration images for degradation levels 1 to 4
demo_image_paths = [
    os.path.abspath("demonstration_img/1.jpg"),
    os.path.abspath("demonstration_img/2.jpg"),
    os.path.abspath("demonstration_img/3.jpg"),
    os.path.abspath("demonstration_img/4.jpg")
]

# Global variables for the main window, image labels, and counters
window = tk.Tk()
window.title("Crater Comparison")
button_press_count = 0  # Counter to track the number of button presses

# Variables for comparison history
comparison_history = []  # List of dictionaries with comparison details
current_comparison_index = -1  # Index in the comparison history

# Initialize variables to store ranking history and variability
ranking_history = []
variability_list = []

# Function to load existing data from a file
def load_existing_data(file_path):
    existing_scores = {image: 0 for image in crater_images}
    existing_counts = {image: 0 for image in crater_images}
    existing_wins = {image: 0 for image in crater_images}
    existing_losses = {image: 0 for image in crater_images}
    existing_draws = {image: 0 for image in crater_images}
    total_button_presses = 0

    if os.path.exists(file_path):
        print(f"Loading existing data from {file_path}")
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
                    print(f"Error parsing line: {line}")
                    print(f"Error: {e}")
                    continue  # Skip the problematic line and continue processing
    else:
        print(f"No existing data found at {file_path}. Starting fresh.")
    return existing_scores, existing_counts, existing_wins, existing_losses, existing_draws, total_button_presses

# Define the output folder globally
output_folder = os.path.join(image_folder, "results")
snapshot_folder = os.path.join(output_folder, "ranking_snapshots")  # New folder for snapshots
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"Created directory: {output_folder}")
if not os.path.exists(snapshot_folder):
    os.makedirs(snapshot_folder)
    print(f"Created directory for snapshots: {snapshot_folder}")

# Load existing data at the start
file_path = os.path.join(output_folder, "sorted_crater_images.txt")
existing_scores, existing_counts, existing_wins, existing_losses, existing_draws, total_button_presses = load_existing_data(file_path)

# Initialize points dictionary to track scores, wins, losses, draws, and counts for each image
image_scores = existing_scores.copy()
image_counts = existing_counts.copy()
image_wins = existing_wins.copy()
image_losses = existing_losses.copy()
image_draws = existing_draws.copy()
button_press_count = total_button_presses  # Continue from the last button press count

# Function to save the sorted sequence of craters with their scores
def save_sorted_sequence():
    try:
        # Define the file path to save the sorted sequence
        global output_folder
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"Created directory: {output_folder}")

        file_path = os.path.join(output_folder, "sorted_crater_images.txt")
        print(f"Saving sorted sequence to: {file_path}")  # Debugging

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

# Function to save rankings at regular intervals and compute variability
def save_rankings_snapshot(count):
    try:
        global snapshot_folder
        if not os.path.exists(snapshot_folder):
            os.makedirs(snapshot_folder)
            print(f"Created directory: {snapshot_folder}")

        # Sort images by their scores
        sorted_images = sorted(image_scores.items(), key=lambda x: x[1], reverse=True)
        # Store the ranking (list of image paths)
        ranking = [img[0] for img in sorted_images]
        # Map image paths to ranks
        current_ranks = {img_path: rank for rank, img_path in enumerate(ranking)}
        # Append to ranking_history
        ranking_history.append((count, current_ranks))

        # Compute variability if there's a previous ranking
        if len(ranking_history) > 1:
            prev_count, prev_ranks = ranking_history[-2]
            # Create arrays of ranks
            ranks_current = []
            ranks_previous = []
            for img_path in crater_images:
                rank_current = current_ranks.get(img_path, len(crater_images))
                rank_previous = prev_ranks.get(img_path, len(crater_images))
                ranks_current.append(rank_current)
                ranks_previous.append(rank_previous)
            # Compute Spearman's rho
            rho, _ = spearmanr(ranks_current, ranks_previous)
            variability = 1 - rho  # Variability inversely related to correlation
            # Append to variability_list
            variability_list.append((count, variability))
            print(f"At {count} comparisons, variability is {variability}")

        # Save the ranking to a file in the snapshots folder
        snapshot_file = os.path.join(snapshot_folder, f"ranking_snapshot_{count}.txt")
        with open(snapshot_file, "w") as f:
            for rank, img_path in enumerate(ranking):
                f.write(f"{rank+1},{os.path.basename(img_path)},{image_scores[img_path]}\n")
        print(f"Saved ranking snapshot at {count} button presses to {snapshot_file}")
    except Exception as e:
        print(f"Error in save_rankings_snapshot: {e}")

# Function to update and save the variability plot in the results folder
def update_variability_plot():
    try:
        if not variability_list:
            print("No variability data to plot.")
            return

        counts = [item[0] for item in variability_list]
        variabilities = [item[1] for item in variability_list]

        ax.clear()
        ax.plot(counts, variabilities, marker='o', linestyle='-')
        ax.set_title('Crater Ranking Stability Over Time')
        ax.set_xlabel('Number of Comparisons')
        ax.set_ylabel('Ranking Variability\n(1 - Spearman\'s rho)')
        ax.grid(True)
        canvas.draw()

        # Save the variability plot in the results folder
        plot_file_path = os.path.join(output_folder, "ranking_stability_plot.png")
        fig.savefig(plot_file_path)
        print(f"Saved variability plot to {plot_file_path}")
        
    except Exception as e:
        print(f"Error in update_variability_plot: {e}")

# Function to update the images for comparison
def update_comparison():
    global current_left_image, current_right_image

    # Get the current comparison from the history
    current_comparison = comparison_history[current_comparison_index]
    current_left_image = os.path.abspath(current_comparison['img1'])
    current_right_image = os.path.abspath(current_comparison['img2'])

    # Load and display images
    try:
        image1 = ImageTk.PhotoImage(Image.open(current_left_image).resize((250, 250)))
        image2 = ImageTk.PhotoImage(Image.open(current_right_image).resize((250, 250)))
        label1.config(image=image1)
        label2.config(image=image2)
        label1.image = image1  # Keep a reference to avoid garbage collection
        label2.image = image2  # Keep a reference to avoid garbage collection
    except Exception as e:
        print(f"Error loading images: {e}")

    # Update button states
    update_navigation_buttons()
def initialize_interface():
    window.columnconfigure(0, weight=1)
    window.columnconfigure(1, weight=4)
    window.columnconfigure(2, weight=4)
    window.columnconfigure(3, weight=4)
    window.rowconfigure([0, 1, 2, 3, 4, 5], weight=1)

    # Frame for demonstration images
    demo_frame = tk.Frame(window)
    demo_frame.grid(row=0, column=0, rowspan=6, sticky='ns')
    
    # Load and display demonstration images with degradation levels
    for i, path in enumerate(demo_image_paths):
        if os.path.exists(path):
            demo_image = ImageTk.PhotoImage(Image.open(path).resize((80, 80)))
            demo_label = tk.Label(demo_frame, image=demo_image)
            demo_label.grid(row=i, column=0, padx=5, pady=5)
            label_text = tk.Label(demo_frame, text=f"Level {i + 1}")
            label_text.grid(row=i, column=1, padx=5, pady=5)
            demo_label.image = demo_image
        else:
            print(f"Demo image not found: {path}")

    # Create labels for the comparison images
    global label1, label2, btn1, btn2, btn_same, btn_last_page, btn_next_page
    label1 = tk.Label(window)
    label1.grid(row=0, column=1, columnspan=1, padx=10, pady=10)
    label2 = tk.Label(window)
    label2.grid(row=0, column=2, columnspan=1, padx=10, pady=10)

    # Create buttons for selecting which image is more degraded or if both are similar
    button_frame = tk.Frame(window)
    button_frame.grid(row=1, column=1, columnspan=2, pady=10)

    btn1 = tk.Button(button_frame, text="Left is More Degraded", command=lambda: select_image(True), width=20)
    btn1.grid(row=0, column=0, padx=5, pady=5)
    btn2 = tk.Button(button_frame, text="Right is More Degraded", command=lambda: select_image(False), width=20)
    btn2.grid(row=0, column=1, padx=5, pady=5)

    # Place the "Both are Similarly Degraded" button below the other two buttons
    btn_same = tk.Button(button_frame, text="Both are Similarly Degraded", command=lambda: select_image(None), width=25)
    btn_same.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

    # Navigation buttons
    nav_frame = tk.Frame(window)
    nav_frame.grid(row=2, column=1, columnspan=2, pady=5)

    btn_last_page = tk.Button(nav_frame, text="Last Page", command=last_page, width=15)
    btn_last_page.grid(row=0, column=0, padx=5, pady=5)
    btn_next_page = tk.Button(nav_frame, text="Next Page", command=next_page, width=15)
    btn_next_page.grid(row=0, column=1, padx=5, pady=5)

    # Create a frame for the variability plot
    global plot_frame, canvas, ax, fig
    plot_frame = tk.Frame(window)
    plot_frame.grid(row=0, column=3, rowspan=6, padx=10, pady=10, sticky='nsew')

    # Initialize the plot
    fig = Figure(figsize=(5, 5), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_title('Crater Ranking Stability Over Time')
    ax.set_xlabel('Number of Comparisons')
    ax.set_ylabel('Ranking Variability\n(1 - Spearman\'s rho)', labelpad=10)  # Add padding to y-label
    ax.grid(True)
    fig.subplots_adjust(left=0.15)  # Adjust the left margin for better y-label visibility
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Start the first comparison
    next_page()
    
    # Save data when the window is closed
    def on_closing():
        print("Closing the application...")
        save_sorted_sequence()  # Save the data before exiting
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_closing)

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

    print(f'Scores updated: {os.path.basename(current_left_image)}: {image_scores[current_left_image]}, {os.path.basename(current_right_image)}: {image_scores[current_right_image]}')
    print(f'Wins/Losses/Draws updated: {os.path.basename(current_left_image)}: {image_wins[current_left_image]}/{image_losses[current_left_image]}/{image_draws[current_left_image]}, {os.path.basename(current_right_image)}: {image_wins[current_right_image]}/{image_losses[current_right_image]}/{image_draws[current_right_image]}')
    print(f'Sample counts updated: {os.path.basename(current_left_image)}: {image_counts[current_left_image]}, {os.path.basename(current_right_image)}: {image_counts[current_right_image]}')
    print(f'Button pressed {button_press_count} times.')

    # Save rankings every N button presses
    N = 15  # Set N to 5 to update variability plot after each click
    if button_press_count % N == 0:
        save_rankings_snapshot(button_press_count)
        update_variability_plot()  # Update the plot in the GUI

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

# Initialize the interface and start the application
initialize_interface()
window.mainloop()
