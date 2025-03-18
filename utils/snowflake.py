import time
import threading

# Snowflake ID Generator
class SnowflakeGenerator:
    def __init__(self, worker_id, datacenter_id=0, sequence=0, twepoch=1609459200000):  # epoch: Jan 1, 2021
        # Bit lengths
        self.worker_id_bits = 5
        self.datacenter_id_bits = 5
        self.sequence_bits = 12
        
        # Max values
        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)
        self.max_datacenter_id = -1 ^ (-1 << self.datacenter_id_bits)
        self.max_sequence = -1 ^ (-1 << self.sequence_bits)
        
        # Validate inputs
        if worker_id > self.max_worker_id or worker_id < 0:
            raise ValueError(f"Worker ID must be between 0 and {self.max_worker_id}")
        if datacenter_id > self.max_datacenter_id or datacenter_id < 0:
            raise ValueError(f"Datacenter ID must be between 0 and {self.max_datacenter_id}")
        
        # Bit shift amounts
        self.worker_id_shift = self.sequence_bits
        self.datacenter_id_shift = self.sequence_bits + self.worker_id_bits
        self.timestamp_shift = self.sequence_bits + self.worker_id_bits + self.datacenter_id_bits
        
        # Initialize state
        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = sequence
        self.twepoch = twepoch
        self.last_timestamp = -1
        
        # Thread safety
        self.lock = threading.Lock()
    
    def _time_gen(self):
        """Get current timestamp in milliseconds."""
        return int(time.time() * 1000)
    
    def _til_next_millis(self, last_timestamp):
        """Wait until next millisecond."""
        timestamp = self._time_gen()
        while timestamp <= last_timestamp:
            timestamp = self._time_gen()
        return timestamp
    
    def next_id(self):
        """Generate the next unique ID."""
        with self.lock:
            timestamp = self._time_gen()
            
            if timestamp < self.last_timestamp:
                raise ValueError(f"Clock moved backwards. Refusing to generate ID")
            
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                if self.sequence == 0:
                    timestamp = self._til_next_millis(self.last_timestamp)
            else:
                self.sequence = 0
            
            self.last_timestamp = timestamp
            
            snowflake_id = (
                ((timestamp - self.twepoch) << self.timestamp_shift) |
                (self.datacenter_id << self.datacenter_id_shift) |
                (self.worker_id << self.worker_id_shift) |
                self.sequence
            )
            
            return snowflake_id

def base62_encode(number, length=7):
    """
    Convert a number to a base62 string of exactly the specified length.
    
    Args:
        number: The number to convert (Snowflake ID)
        length: The desired length of the output string (default: 7)
        
    Returns:
        A base62 string of exactly the specified length
    """
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    base = len(chars)
    result = ""
    
    # Convert to base62
    temp_number = number
    while temp_number > 0:
        result = chars[temp_number % base] + result
        temp_number //= base
    
    # Handle zero case
    if result == "":
        result = "0"
    
    # Ensure exact length
    if len(result) < length:
        # Pad with leading zeros (or another character if preferred)
        result = chars[0] * (length - len(result)) + result
    elif len(result) > length:
        # If longer than desired, take the last 'length' characters
        result = result[-length:]
    
    return result

def generate_short_code_from_snowflake(worker_id=1, datacenter_id=0):
    """
    Generate a short URL code using a Snowflake ID converted to base62.
    
    Args:
        worker_id: ID of the worker (server instance)
        datacenter_id: ID of the datacenter
        
    Returns:
        A 7-character base62 string
    """
    # Initialize Snowflake generator
    snowflake = SnowflakeGenerator(worker_id=worker_id, datacenter_id=datacenter_id)
    
    # Generate Snowflake ID
    snowflake_id = snowflake.next_id()
    
    # Convert to fixed-length base62 string
    return base62_encode(snowflake_id, length=7)

# Example usage
# if __name__ == "__main__":
#     # Generate a few short codes to demonstrate
#     for i in range(5):
#         short_code = generate_short_code_from_snowflake(worker_id=1)
#         print(f"Generated short code: {short_code}")
#         # Small delay to see different timestamps
#         time.sleep(0.1)