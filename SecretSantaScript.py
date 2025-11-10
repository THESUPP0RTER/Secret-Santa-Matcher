import random as r
from itertools import cycle


participants_file = "participantnames.txt"
with open(participants_file) as f:
    participants = f.read().splitlines()

admins_file = "admins.txt"
with open(admins_file) as f:
    admins = f.read().splitlines() 

#Adjust Banlist, prevent any repeats
banlist = {
    "Person1" : ["BannedPerson"],
}

def can_give_to(giver, receiver, banlist):
    """Check if giver can give to receiver based on banlist"""
    if giver == receiver:
        return False
    if receiver in banlist.get(giver, []):
        return False
    return True


def find_hamiltonian_cycle(participants, banlist, seed=None):
    """Find a single cycle that includes all participants"""
    # Sort participants for consistent starting point
    sorted_participants = sorted(participants)

    if seed is not None:
        r.seed(seed)

    # Try multiple starting points and orderings
    max_attempts = 1000
    for attempt in range(max_attempts):
        shuffled = sorted_participants.copy()
        r.shuffle(shuffled)

        # Try to build a cycle starting from the first person
        path = [shuffled[0]]
        visited = {shuffled[0]}
        remaining = set(shuffled[1:])

        if build_cycle(path, visited, remaining, banlist, shuffled[0], use_random=True):
            # Convert path to assignments dictionary
            assignments = {}
            for i in range(len(path)):
                giver = path[i]
                receiver = path[(i + 1) % len(path)]  # Wrap around to form cycle
                assignments[giver] = receiver
            return assignments

    return None


def build_cycle(path, visited, remaining, banlist, start_person, use_random=True):
    """Recursively build a Hamiltonian cycle"""
    current = path[-1]

    # If we've visited everyone, check if we can close the cycle
    if not remaining:
        # Can the last person give to the first person to close the cycle?
        return can_give_to(current, start_person, banlist)

    # Try each remaining person
    remaining_list = sorted(list(remaining))  # Sort for determinism
    if use_random:
        r.shuffle(remaining_list)

    for next_person in remaining_list:
        if can_give_to(current, next_person, banlist):
            # Try adding this person to the path
            path.append(next_person)
            visited.add(next_person)
            remaining.remove(next_person)

            if build_cycle(path, visited, remaining, banlist, start_person, use_random):
                return True

            # Backtrack
            path.pop()
            visited.remove(next_person)
            remaining.add(next_person)

    return False


def secret_santa_matcher(participants, banlist, seed=None):
    """Match Secret Santa participants in a single cycle"""
    return find_hamiltonian_cycle(participants, banlist, seed)


def split_assignments_for_admins(assignments, admin1, admin2):
    """Split assignments so each admin can't see their own pairing (as giver or receiver)"""
    all_assignments = list(assignments.items())

    admin1_list = []
    admin2_list = []
    shared = []  # Assignments neither admin is involved in

    for giver, receiver in all_assignments:
        involves_admin1 = (giver == admin1 or receiver == admin1)
        involves_admin2 = (giver == admin2 or receiver == admin2)

        if not involves_admin1 and not involves_admin2:
            # Neither admin involved - both could distribute this
            shared.append((giver, receiver))
        elif not involves_admin1:
            # Only admin2 involved - only admin1 can distribute
            admin1_list.append((giver, receiver))
        elif not involves_admin2:
            # Only admin1 involved - only admin2 can distribute
            admin2_list.append((giver, receiver))
        # If both involved, neither can distribute (shouldn't happen in a cycle)

    # Split the shared assignments roughly in half
    mid = len(shared) // 2
    admin1_list.extend(shared[:mid])
    admin2_list.extend(shared[mid:])

    return admin1_list, admin2_list


# Get seed from user
seed_input = input("Enter seed number: ")
try:
    seed = int(seed_input)
except ValueError:
    print("Invalid seed. Using default seed 67")
    seed = 67

# Display admin choices
print("\nWho are you?")
for i, admin in enumerate(admins, 1):
    print(f"{i}. {admin}")

# Get admin selection
admin_choice = input("\nEnter your number: ")
try:
    choice_index = int(admin_choice) - 1
    if choice_index < 0 or choice_index >= len(admins):
        print("Invalid choice. Exiting.")
        exit(1)
except ValueError:
    print("Invalid input. Exiting.")
    exit(1)

selected_admin = admins[choice_index]

# Run the matcher with the seed
assignments = secret_santa_matcher(participants, banlist, seed=seed)

if assignments:
    # Generate assignments for both admins
    if len(admins) >= 2:
        admin1 = admins[0]
        admin2 = admins[1]

        admin1_list, admin2_list = split_assignments_for_admins(
            assignments, admin1, admin2
        )

        admin_assignments_map = {
            admin1: admin1_list,
            admin2: admin2_list
        }

        # Show only the selected admin's assignments
        if selected_admin in admin_assignments_map:
            print("\n" + "=" * 40)
            print(f"ASSIGNMENTS FOR {selected_admin.upper()} TO DISTRIBUTE:")
            print("=" * 40)
            for giver, receiver in admin_assignments_map[selected_admin]:
                print(f"{giver} → {receiver}")
            print("\n" + "=" * 40)
            print(f"Distribute these assignments to the people listed.")
            print("You won't see your own Secret Santa assignment!")
        else:
            print(f"No assignments found for {selected_admin}")
    else:
        print("Need at least 2 admins in admins.txt")
else:
    print("Could not find a valid assignment. Try adjusting the banlist.")
