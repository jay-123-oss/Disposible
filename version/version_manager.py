"""Semantic version manager."""
def bump_version(current="1.0.0", bump_type="minor"):
    major, minor, patch = map(int, current.split("."))
    if bump_type == "major":
        return f"{major+1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor+1}.0"
    else:
        return f"{major}.{minor}.{patch+1}"

if __name__ == "__main__":
    print("New version:", bump_version())
