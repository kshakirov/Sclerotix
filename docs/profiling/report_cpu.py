#!/usr/bin/env python3

import argparse
import json
from collections import defaultdict
from pathlib import Path


def frame_label(frame):
    name = frame.get("name", "<unknown>")
    file = frame.get("file")
    line = frame.get("line")
    if not file:
        return name
    if line is None:
        return f"{name}:{file}"
    return f"{name}:{file}:{line}"


def collect(profile_path):
    with profile_path.open(encoding="utf-8") as source:
        document = json.load(source)

    frames = document["shared"]["frames"]
    self_weight = defaultdict(float)
    inclusive_weight = defaultdict(float)
    total_weight = 0.0

    for profile in document["profiles"]:
        if profile.get("type") != "sampled":
            continue
        samples = profile.get("samples", [])
        weights = profile.get("weights") or [1.0] * len(samples)
        for stack, weight in zip(samples, weights):
            if not stack:
                continue
            weight = float(weight)
            total_weight += weight
            leaf = frame_label(frames[stack[-1]])
            self_weight[leaf] += weight
            for frame_index in set(stack):
                inclusive_weight[frame_label(frames[frame_index])] += weight

    if not total_weight:
        raise SystemExit(f"No sampled stacks found in {profile_path}")
    return total_weight, self_weight, inclusive_weight


def print_ranking(title, weights, total_weight, top):
    print(f"\n{title}")
    print(f"{'samples %':>9}  location")
    for location, weight in sorted(
        weights.items(), key=lambda item: item[1], reverse=True
    )[:top]:
        print(f"{weight / total_weight * 100:>8.2f}%  {location}")


def main():
    parser = argparse.ArgumentParser(
        description="Print self and inclusive rankings from a SpeedScope CPU profile."
    )
    parser.add_argument("profile", type=Path)
    parser.add_argument("--top", type=int, default=30)
    args = parser.parse_args()
    if args.top < 1:
        parser.error("--top must be positive")

    total, self_weight, inclusive_weight = collect(args.profile)
    print(f"PROFILE: {args.profile.resolve()}")
    print(f"Total sample weight: {total:g}")
    print_ranking("TOP SELF", self_weight, total, args.top)
    print_ranking("TOP INCLUSIVE", inclusive_weight, total, args.top)


if __name__ == "__main__":
    main()
