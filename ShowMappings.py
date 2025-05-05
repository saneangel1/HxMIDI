import json
import matplotlib.pyplot as plt
import os # Import os to handle file paths
import argparse # Import argparse for command-line arguments

def read_and_extract_router_data(json_file_path):
    """
    Reads the router JSON file, extracts the first 15 entries from the 'Router' array,
    interprets them as input-to-output mappings, prints a text diagram,
    Args:
        json_file_path (str): The path to the JSON file.
    Returns:
        dict: A dictionary representing the mappings {input_num: [output_num1, output_num2,...]}, or None on error.
    """
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)  # Load the entire JSON data
    except FileNotFoundError:
        print(f"Error: File not found. The file '{json_file_path}' does not exist.")
        return  # Exit the function if the file is not found
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON. The file '{json_file_path}' is not valid JSON:\n{e}")
        return  # Exit if the JSON is invalid
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return  # Exit for other errors
        return None

    # Check if the 'Router' key exists in the data
    if 'Router' not in data:
        print(f"Error: The JSON file does not contain a 'Router' key.")
        return  # Exit if the key is not found
        return None

    router_data = data['Router']  # Get the 'Router' array

    if not isinstance(router_data, list):
        print(f"Error: 'Router' key does not contain a list.")
        return
        return None

    # Extract the first 15 entries, handling cases where the array has fewer than 15
    first_15_router_entries = router_data[:15]

    print("MIDI Input/Output Mappings (First 15):")
    print("-" * 40)
    mappings = {} # Dictionary to store the mappings for drawing

    for i, value in enumerate(first_15_router_entries):
        input_num = i + 1
        try:
            # Convert the value from the JSON (which might be a string) to an integer
            int_value = int(value, 16) # Specify base 16 for hexadecimal conversion
        except (ValueError, TypeError):
            print(f"Warning: Input {input_num} has non-integer value '{value}'. Skipping.")
            continue # Skip to the next input if conversion fails

        connected_outputs = []
        for j in range(15):  # Check bits 0 to 14 for outputs 1 to 15
            if (int_value >> j) & 1: # Use the integer value for the bitwise operation
                output_num = j + 1
                connected_outputs.append(output_num) # Store output number

        mappings[input_num] = connected_outputs # Store in the dictionary
        # Print the textual representation
        output_str_list = [f"Output {o}" for o in connected_outputs]
        print(f"Input {input_num:2d} -> {', '.join(output_str_list) if output_str_list else 'None'}")

    return mappings

def load_midi_names(names_json_path):
    """
    Loads MIDI device names from a JSON file.
    The JSON file is expected to have string keys ("1", "2", ...) mapping to string names.
    It also looks for an "Order" key with a comma-separated list of numbers.
    The JSON file is expected to have string keys ("1", "2", ...) mapping to string names.

    Args:
        names_json_path (str): The path to the MIDI names JSON file.

    Returns:
        tuple: A tuple containing:
               - dict: Mapping of integer port numbers to names {1: "Name1", ...}.
               - list: A list of integers representing the desired node order, or None if not found/invalid.
              or an empty dictionary if loading fails.
    """
    names = {}
    try:
        with open(names_json_path, 'r') as f:
            raw_names = json.load(f)
        order_list = None
        # Convert string keys to integers and store
        for key, name in raw_names.items():
            try:
                port_num = int(key)
                names[port_num] = name
            except (ValueError, TypeError): # Catch if key is not a number-like string
                # Ignore non-numeric keys like "Order" here
                pass

        # Process the "Order" key if it exists
        if "Order" in raw_names and isinstance(raw_names["Order"], str):
            try:
                order_list = [int(num_str.strip()) for num_str in raw_names["Order"].split(',') if num_str.strip()]
                # Validate numbers are within expected range (optional but good practice)
                order_list = [num for num in order_list if 1 <= num <= 15]
                if not order_list: # Handle case where Order string was empty or invalid after parsing
                    order_list = None
            except ValueError:
                print(f"Warning: Could not parse numbers in 'Order' key in '{names_json_path}'. Using default order.")
                order_list = None
            print(f"Successfully loaded names from: {names_json_path}")
    except FileNotFoundError:
        print(f"Warning: Names file not found at '{names_json_path}'. Using default labels.")
        return {}, None # Return empty names and no order
    except Exception as e:
        print(f"Warning: An unexpected error occurred loading names from '{names_json_path}': {e}. Using default labels.")
        return names
        return names, None # Return potentially partial names, no order
    return names, order_list

def draw_mapping_diagram(mappings, midi_names, order_list, output_image_path, router_filename):
    """
    Draws a diagram of the mappings using Matplotlib and saves it to a file.

    Args:
        mappings (dict): The mapping dictionary {input_num: [output_num1, ...]}.
        midi_names (dict): Dictionary mapping port numbers to names {1: "Name1", ...}.
        router_filename (str): The base name of the router JSON file for the title.
        order_list (list | None): Optional list defining the vertical order of nodes.
        output_image_path (str): The path to save the output image file (e.g., PNG).
    """
    if not mappings:
        print("No mappings provided to draw.")
        return

    num_nodes = 15
    fig, ax = plt.subplots(figsize=(10, 12)) # Increased size slightly for potentially longer names

    # Node positions
    input_x = 0
    output_x = 1
    num_slots = num_nodes # Use 15 vertical slots
    y_spacing = 1.0 / (num_slots + 1)

    # Determine vertical position index for each node
    node_to_y_index = {}
    ordered_nodes_set = set()
    current_y_index = 0

    if order_list:
        for node_num in order_list:
            if 1 <= node_num <= num_nodes and node_num not in node_to_y_index: # Ensure valid and not already placed
                node_to_y_index[node_num] = current_y_index
                ordered_nodes_set.add(node_num)
                current_y_index += 1

    # Place remaining nodes
    all_nodes_set = set(range(1, num_nodes + 1))
    remaining_nodes = sorted(list(all_nodes_set - ordered_nodes_set))

    for node_num in remaining_nodes:
        if node_num not in node_to_y_index: # Should always be true here, but safe check
             node_to_y_index[node_num] = current_y_index
             current_y_index += 1
    # Draw nodes and labels
    for node_num in range(1, num_nodes + 1):
        y_index = node_to_y_index.get(node_num, -1) # Get the calculated vertical index
        if y_index == -1: continue # Should not happen with current logic, but safety check

        y = 1.0 - (y_index + 1) * y_spacing # Calculate y-coordinate based on index
        # Get name or use default, handle empty strings
        # Get name from dictionary. Will be None if not found or empty string if present but blank.
        node_label = midi_names.get(node_num)
        # Input node
        ax.plot(input_x, y, 'bo', markersize=10) # Blue circle for input

       # Only draw label text if the name exists and is not empty
        if node_label: # Checks if name is not None and not an empty string
            ax.text(input_x - 0.05, y, node_label, ha='right', va='center')
        # Output node
        ax.plot(output_x, y, 'rs', markersize=10) # Red square for output
        # Only draw label text if the name exists and is not empty
        if node_label: # Checks if name is not None and not an empty string
            ax.text(output_x + 0.05, y, node_label, ha='left', va='center')

    # Draw connections
    for input_num, output_nums in mappings.items():
        input_y_index = node_to_y_index.get(input_num, -1)
        input_name = midi_names.get(input_num) # Get input name
        if input_y_index == -1: continue # Skip if input node wasn't placed
        input_y = 1.0 - (input_y_index + 1) * y_spacing
        input_name = midi_names.get(input_num) # Get input name
        for output_num in output_nums:
            output_y_index = node_to_y_index.get(output_num, -1)
            output_name = midi_names.get(output_num) # Get output name
            if output_y_index == -1: continue # Skip if output node wasn't placed
            output_y = 1.0 - (output_y_index + 1) * y_spacing

            # Only draw the line if BOTH input and output have a non-empty name
            if input_name and output_name: # Checks if names are not None and not empty strings
                ax.plot([input_x, output_x], [input_y, output_y], 'k-', alpha=0.6) # Black line

    # Customize plot
    ax.set_xlim(-0.3, 1.3)
    ax.set_ylim(0, 1.1)
    # ax.set_title(f'MIDI Mappings: {router_filename}') # Removed title from top
    ax.axis('off') # Hide axes

    # Save the figure
    try:
        plt.savefig(output_image_path, bbox_inches='tight')
        print(f"\nDiagram saved successfully to: {output_image_path}")
    except Exception as e:
        print(f"\nError saving diagram to {output_image_path}: {e}")

    # Add title at the bottom using figure coordinates (relative to the whole figure)
    fig.text(0.5, 0.01, f'MIDI Mappings: {router_filename}', ha='center', va='bottom', fontsize=plt.rcParams['axes.titlesize'])

    plt.close(fig) # Close the plot figure to free memory

def draw_mapping_matrix(mappings, midi_names, order_list, output_image_path, router_filename):
    """
    Draws a matrix diagram of the mappings using Matplotlib and saves it to a file.

    Args:
        mappings (dict): The mapping dictionary {input_num: [output_num1, ...]}.
        midi_names (dict): Dictionary mapping port numbers to names {1: "Name1", ...}.
        router_filename (str): The base name of the router JSON file for the title.
        order_list (list | None): Optional list defining the order for axes.
        output_image_path (str): The path to save the output image file (e.g., PNG).
    """
    if not mappings:
        print("No mappings provided to draw matrix.")
        return

    # --- Check if a valid order list is provided ---
    if not order_list:
        print("Error: No valid 'Order' key found in names file. Cannot draw matrix based on order.")
        return

    # The nodes to display are exactly those in the order_list
    display_nodes_ordered = order_list
    num_displayed_nodes = len(display_nodes_ordered)

    if num_displayed_nodes == 0:
        print("Error: The 'Order' list is empty. Cannot draw matrix.")
        return

    fig, ax = plt.subplots(figsize=(4, 4)) # Square figure often works well for matrices

    # --- Determine axis positions based *only* on the order_list ---
    # Maps node number (from order_list) to display index (0 to num_displayed_nodes-1)
    node_to_display_index = {node_num: index for index, node_num in enumerate(display_nodes_ordered)}

    # Create lists of labels in the correct display order
    ordered_labels = [midi_names.get(node_num, f"Node {node_num}") for node_num in display_nodes_ordered] # Use default if name missing

    # --- Plot the connection points ---
    x_coords = []
    y_coords = []
    for input_num, output_nums in mappings.items():
        # Check if the input node is in our ordered list
        input_index = node_to_display_index.get(input_num)
        if input_index is not None: # If input_num is in the order list...
            for output_num in output_nums:
                # Check if the output node is also in our ordered list
                output_index = node_to_display_index.get(output_num)
                if output_index is not None: # If output_num is in the order list...
                    # We plot at the *display index* coordinates
                    x_coords.append(input_index)
                    y_coords.append(output_index)

    # Use scatter for individual points, easier than managing a full matrix image
    ax.scatter(x_coords, y_coords, marker='s', s=100, c='black', zorder=3) # Black squares

    # --- Configure Axes ---
    ax.set_xticks(range(num_displayed_nodes))
    ax.set_yticks(range(num_displayed_nodes))

    ax.set_xticklabels(ordered_labels, rotation=90) # Use ordered labels, rotate for readability
    ax.set_yticklabels(ordered_labels)

    # Move ticks and labels
    ax.xaxis.tick_top()
    ax.yaxis.tick_right()
    ax.xaxis.set_label_position('top')
    ax.yaxis.set_label_position('right')

    ax.set_xlim(-0.5, num_displayed_nodes - 0.5) # Adjust limits to number of displayed nodes
    ax.set_ylim(num_displayed_nodes - 0.5, -0.5) # Adjust limits and invert y-axis

    ax.set_xlabel("Inputs", labelpad=15) # Add padding
    ax.set_ylabel("Outputs", labelpad=15) # Add padding
    # ax.set_title(f'MIDI Mapping Matrix: {router_filename}') # Removed title from top

    # Add grid lines
    ax.grid(True, which='both', color='gray', linestyle='-', linewidth=2.0)
    ax.set_aspect('equal', adjustable='box') # Make cells square

    # Add title at the bottom using figure coordinates
    fig.text(1.15, 1.15, router_filename, ha='right', va='top', fontweight='bold', fontsize=plt.rcParams['axes.titlesize'])

    # --- Save the figure ---
    try:
        plt.savefig(output_image_path, bbox_inches='tight')
        print(f"\nMatrix diagram saved successfully to: {output_image_path}")
    except Exception as e:
        print(f"\nError saving matrix diagram to {output_image_path}: {e}")


    plt.close(fig) # Close the plot figure

if __name__ == "__main__":
    # --- Command Line Argument Parsing ---
    parser = argparse.ArgumentParser(description="Generate a mapping diagram from a MIDI router JSON file.")
    parser.add_argument("router_json_path", help="Path to the input router JSON file.")
    parser.add_argument("-n", "--names", help="Path to the MIDI names JSON file (defaults to 'y:\\Projects\\HxMIDI\\MIDI-Names.json').")
    parser.add_argument("-o", "--output", help="Path to save the output diagram image (e.g., mappings.png). If omitted, defaults to a path based on the input filename.")

    args = parser.parse_args()
    router_json_path = args.router_json_path
    router_filename = os.path.splitext(os.path.basename(router_json_path))[0] # Get filename without extension
    # --- End Argument Parsing ---

    mappings = read_and_extract_router_data(router_json_path)

    if mappings:
        # Define the path to the names file (using the provided absolute path)
        # Use the path from command line if provided, otherwise use the default
        if args.names:
            names_json_path = args.names
        else:
            names_json_path = r"y:\Projects\HxMIDI\MIDI-Names.json" # Default path

        midi_names, order_list = load_midi_names(names_json_path) # Unpack names and order

        # Suggest an output filename based on the input filename
        base_output_path = args.output # Get base path from args if provided
        if not base_output_path:
            # If -o not used, create default base path without extension
            base_name = os.path.splitext(os.path.basename(router_json_path))[0]
            base_output_path = os.path.join(os.path.dirname(router_json_path), base_name)
        else:
            # If -o is used, remove common image extensions to get a base name
            base_output_path = os.path.splitext(base_output_path)[0]

        # Use the output path from command line if provided, otherwise use default
        # Define specific paths for each diagram type
        diagram_output_path = base_output_path + "_diagram.png"
        matrix_output_path = base_output_path + "_matrix.png"

        # Ensure the output path is absolute if the input was relative
        if not os.path.isabs(diagram_output_path):
             diagram_output_path = os.path.abspath(diagram_output_path)
        if not os.path.isabs(matrix_output_path):
             matrix_output_path = os.path.abspath(matrix_output_path)

        # --- Generate Line Diagram ---
        print(f"Attempting to save line diagram to: {diagram_output_path}")
        draw_mapping_diagram(mappings, midi_names, order_list, diagram_output_path, router_filename)

        # --- Generate Matrix Diagram ---
        print(f"Attempting to save matrix diagram to: {matrix_output_path}")
        draw_mapping_matrix(mappings, midi_names, order_list, matrix_output_path, router_filename)
