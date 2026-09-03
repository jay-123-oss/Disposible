"""Raft Consensus Algorithm Core Implementation for Distributed Layer.

Implements:
- Raft Roles: FOLLOWER, CANDIDATE, LEADER
- Log Entries with terms, indices, and commands
- RequestVote and AppendEntries RPC protocols
- Leader election, heartbeat handling, and commit management
"""

from __future__ import annotations

import enum
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("FractalCore.Distributed.Raft")


class RaftRole(str, enum.Enum):
    """Roles assumed by a Raft cluster node."""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class RaftLogEntry:
    """Individual entry in a Raft node's replicated log."""
    term: int
    index: int
    command: Any
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "term": self.term,
            "index": self.index,
            "command": self.command,
            "timestamp": self.timestamp,
        }


@dataclass
class RequestVoteArgs:
    """Arguments for RequestVote RPC."""
    term: int
    candidate_id: str
    last_log_index: int
    last_log_term: int


@dataclass
class RequestVoteReply:
    """Results returned from RequestVote RPC."""
    term: int
    vote_granted: bool
    reason: str = ""


@dataclass
class AppendEntriesArgs:
    """Arguments for AppendEntries (and heartbeat) RPC."""
    term: int
    leader_id: str
    prev_log_index: int
    prev_log_term: int
    entries: List[RaftLogEntry]
    leader_commit: int


@dataclass
class AppendEntriesReply:
    """Results returned from AppendEntries RPC."""
    term: int
    success: bool
    match_index: int = 0
    reason: str = ""


class RaftEngine:
    """Core Raft state machine handling terms, elections, heartbeats, and log commits."""

    def __init__(
        self,
        node_id: str,
        peers: Optional[List[str]] = None,
        election_timeout_ms: int = 1000,
        heartbeat_interval_ms: int = 500,
        log_retention: int = 10000,
    ) -> None:
        self.node_id = node_id
        self.peers = peers or []
        self.election_timeout_ms = election_timeout_ms
        self.heartbeat_interval_ms = heartbeat_interval_ms
        self.log_retention = log_retention

        # Persistent state on all servers
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log: List[RaftLogEntry] = []

        # Volatile state on all servers
        self.commit_index = 0
        self.last_applied = 0
        self.role = RaftRole.FOLLOWER
        self.current_leader: Optional[str] = None
        self.last_heartbeat = time.time()

        # Volatile state on leaders
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}

        # Election tracking
        self.votes_received: Set[str] = set()

    def get_last_log_index(self) -> int:
        return self.log[-1].index if self.log else 0

    def get_last_log_term(self) -> int:
        return self.log[-1].term if self.log else 0

    def reset_election_timeout(self) -> float:
        jitter = random.uniform(0.8, 1.2)
        timeout = (self.election_timeout_ms / 1000.0) * jitter
        self.last_heartbeat = time.time()
        return timeout

    def start_election(self) -> RequestVoteArgs:
        """Promote self to CANDIDATE and initiate leader election."""
        self.role = RaftRole.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}
        self.current_leader = None
        self.reset_election_timeout()

        logger.info("Node %s started election for term %d", self.node_id, self.current_term)
        return RequestVoteArgs(
            term=self.current_term,
            candidate_id=self.node_id,
            last_log_index=self.get_last_log_index(),
            last_log_term=self.get_last_log_term(),
        )

    def handle_request_vote(self, args: RequestVoteArgs) -> RequestVoteReply:
        """Handle incoming RequestVote RPC according to Raft rules."""
        if args.term > self.current_term:
            self.current_term = args.term
            self.role = RaftRole.FOLLOWER
            self.voted_for = None
            self.current_leader = None

        vote_granted = False
        reason = ""

        if args.term < self.current_term:
            reason = f"Candidate term {args.term} < local term {self.current_term}"
        elif self.voted_for in (None, args.candidate_id):
            last_index = self.get_last_log_index()
            last_term = self.get_last_log_term()
            log_ok = (args.last_log_term > last_term) or (
                args.last_log_term == last_term and args.last_log_index >= last_index
            )
            if log_ok:
                vote_granted = True
                self.voted_for = args.candidate_id
                self.reset_election_timeout()
                reason = "Vote granted"
            else:
                reason = "Candidate log not up-to-date"
        else:
            reason = f"Already voted for {self.voted_for} in term {self.current_term}"

        return RequestVoteReply(term=self.current_term, vote_granted=vote_granted, reason=reason)

    def record_vote(self, voter_id: str, reply: RequestVoteReply) -> bool:
        """Process incoming vote reply. Returns True if majority acquired and became LEADER."""
        if self.role != RaftRole.CANDIDATE:
            return False

        if reply.term > self.current_term:
            self.current_term = reply.term
            self.role = RaftRole.FOLLOWER
            self.voted_for = None
            return False

        if reply.vote_granted and reply.term == self.current_term:
            self.votes_received.add(voter_id)
            quorum = ((len(self.peers) + 1) // 2) + 1
            if len(self.votes_received) >= quorum:
                self.become_leader()
                return True
        return False

    def become_leader(self) -> None:
        """Transition from Candidate to Leader and initialize leader indices."""
        self.role = RaftRole.LEADER
        self.current_leader = self.node_id
        last_index = self.get_last_log_index()
        for p in self.peers:
            self.next_index[p] = last_index + 1
            self.match_index[p] = 0
        logger.info("Node %s became cluster LEADER for term %d", self.node_id, self.current_term)

    def append_command(self, command: Any) -> RaftLogEntry:
        """Leader appends a client command to its log."""
        if self.role != RaftRole.LEADER:
            raise RuntimeError(f"Cannot append command: node {self.node_id} is not leader (current: {self.current_leader})")
        new_index = self.get_last_log_index() + 1
        entry = RaftLogEntry(term=self.current_term, index=new_index, command=command)
        self.log.append(entry)
        if len(self.log) > self.log_retention:
            self.log = self.log[-self.log_retention:]
        return entry

    def create_append_entries(self, peer_id: str, entries: Optional[List[RaftLogEntry]] = None) -> AppendEntriesArgs:
        """Generate AppendEntries payload (or heartbeat if entries is None) for a peer."""
        prev_idx = self.next_index.get(peer_id, 1) - 1
        prev_term = 0
        if prev_idx > 0:
            for e in reversed(self.log):
                if e.index == prev_idx:
                    prev_term = e.term
                    break

        to_send = entries if entries is not None else [e for e in self.log if e.index > prev_idx]
        return AppendEntriesArgs(
            term=self.current_term,
            leader_id=self.node_id,
            prev_log_index=prev_idx,
            prev_log_term=prev_term,
            entries=to_send,
            leader_commit=self.commit_index,
        )

    def handle_append_entries(self, args: AppendEntriesArgs) -> AppendEntriesReply:
        """Process incoming AppendEntries or heartbeat RPC from a leader."""
        if args.term > self.current_term:
            self.current_term = args.term
            self.role = RaftRole.FOLLOWER
            self.voted_for = None

        if args.term < self.current_term:
            return AppendEntriesReply(
                term=self.current_term,
                success=False,
                reason=f"Leader term {args.term} < local term {self.current_term}",
            )

        # Valid heartbeat/append
        self.role = RaftRole.FOLLOWER
        self.current_leader = args.leader_id
        self.reset_election_timeout()

        # Log consistency check
        if args.prev_log_index > 0:
            matching = [e for e in self.log if e.index == args.prev_log_index]
            if not matching or matching[-1].term != args.prev_log_term:
                return AppendEntriesReply(
                    term=self.current_term,
                    success=False,
                    reason="Log term mismatch at prev_log_index",
                )

        # Append new entries not already in log
        for new_entry in args.entries:
            existing = [e for e in self.log if e.index == new_entry.index]
            if existing:
                if existing[0].term != new_entry.term:
                    self.log = [e for e in self.log if e.index < new_entry.index]
                    self.log.append(new_entry)
            else:
                self.log.append(new_entry)

        # Advance commit index
        if args.leader_commit > self.commit_index:
            self.commit_index = min(args.leader_commit, self.get_last_log_index())

        return AppendEntriesReply(
            term=self.current_term,
            success=True,
            match_index=self.get_last_log_index(),
            reason="Append entries applied",
        )

    def advance_leader_commit(self) -> int:
        """Check match_index of all peers and commit entries replicated on quorum."""
        if self.role != RaftRole.LEADER:
            return self.commit_index

        last_index = self.get_last_log_index()
        quorum = ((len(self.peers) + 1) // 2) + 1

        for n in range(last_index, self.commit_index, -1):
            matches = 1  # leader itself
            for peer in self.peers:
                if self.match_index.get(peer, 0) >= n:
                    matches += 1
            if matches >= quorum:
                # Only commit log entries from current term
                entry = next((e for e in self.log if e.index == n), None)
                if entry and entry.term == self.current_term:
                    self.commit_index = n
                    break
        return self.commit_index

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic snapshot of the Raft state machine."""
        return {
            "node_id": self.node_id,
            "role": self.role.value,
            "current_term": self.current_term,
            "current_leader": self.current_leader,
            "commit_index": self.commit_index,
            "last_log_index": self.get_last_log_index(),
            "last_log_term": self.get_last_log_term(),
            "voted_for": self.voted_for,
            "peers": self.peers,
            "log_entries_count": len(self.log),
        }
