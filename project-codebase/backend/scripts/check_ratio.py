
import difflib

target = "icici lombard ga consulting ms - t & m"
official = "ICICI Lombard GA Consulting MS-T&M"

ratio = difflib.SequenceMatcher(None, target, official).ratio()
print(f"Ratio: {ratio}")

matches = difflib.get_close_matches(target, [official], n=1, cutoff=0.6)
print(f"Match found with 0.6 cutoff? {bool(matches)}")
