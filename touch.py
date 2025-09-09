def fibonacci(n):
    """Generate fibonacci sequence up to n numbers."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    sequence = [0, 1]
    for i in range(2, n):
        next_num = sequence[i-1] + sequence[i-2]
        sequence.append(next_num)
    
    return sequence

# Example usage
if __name__ == "__main__":
    n = int(input("Enter number of fibonacci numbers: "))
    result = fibonacci(n)
    print(f"Fibonacci sequence: {result}")

// ==================================================
// JavaScript Binary Search Function
// ==================================================

function binarySearch(arr, target) {
    /**
     * Perform binary search on a sorted array
     * @param {number[]} arr - Sorted array to search
     * @param {number} target - Value to find
     * @returns {number} Index of target or -1 if not found
     */
    let left = 0;
    let right = arr.length - 1;
    
    while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        
        if (arr[mid] === target) {
            return mid;
        } else if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    
    return -1; // Target not found
}

// Example usage
const sortedArray = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19];
const target = 7;
const result = binarySearch(sortedArray, target);

if (result !== -1) {
    console.log(`Target ${target} found at index ${result}`);
} else {
    console.log(`Target ${target} not found in array`);
}