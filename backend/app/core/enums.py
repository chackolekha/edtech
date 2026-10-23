import enum


class Role(str, enum.Enum):
    student = "student"
    mentor = "mentor"
    provider = "provider"
    admin = "admin"


class VerificationStatus(str, enum.Enum):
    none = "none"
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class MemberRole(str, enum.Enum):
    member = "member"
    moderator = "moderator"
    lead = "lead"


class RequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    ended = "ended"


class ApplicationStatus(str, enum.Enum):
    submitted = "submitted"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"


class ListingStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    closed = "closed"
    completed = "completed"


class WorkspaceStatus(str, enum.Enum):
    active = "active"
    submitted = "submitted"
    completed = "completed"


class TaskStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class MilestoneStatus(str, enum.Enum):
    pending = "pending"
    done = "done"


class DeliverableStatus(str, enum.Enum):
    submitted = "submitted"
    approved = "approved"
    changes_requested = "changes_requested"


class FlagStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"
    dismissed = "dismissed"


class EnrollmentStatus(str, enum.Enum):
    enrolled = "enrolled"
    completed = "completed"


class Visibility(str, enum.Enum):
    public = "public"
    private = "private"


class ProfessionalStatus(str, enum.Enum):
    student = "student"
    recent_graduate = "recent_graduate"
    employed = "employed"
    seeking = "seeking"
    freelance = "freelance"


class ExperienceKind(str, enum.Enum):
    work = "work"
    internship = "internship"
    volunteering = "volunteering"


class Purpose(str, enum.Enum):
    find_projects = "find_projects"
    find_mentor = "find_mentor"
    learn_skills = "learn_skills"
    networking = "networking"
    build_portfolio = "build_portfolio"
    career_guidance = "career_guidance"


class MeetingFormat(str, enum.Enum):
    video = "video"
    chat = "chat"
    in_person = "in_person"


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    declined = "declined"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class ListingKind(str, enum.Enum):
    project = "project"
    guided_project = "guided_project"


REACTABLE_TYPES = ("post", "comment")
FLAGGABLE_TYPES = ("post", "comment", "profile", "listing")
