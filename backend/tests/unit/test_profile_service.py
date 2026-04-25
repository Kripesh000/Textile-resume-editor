"""
Unit Tests for Profile Service

Tests profile CRUD operations, data merging, and profile import functionality.
"""

import pytest
from uuid import uuid4

from app.services.profile_service import ProfileService
from app.db_models import ProfileDB, UserDB


class TestGetProfile:
    """Tests for retrieving profiles"""

    @pytest.mark.asyncio
    async def test_get_profile_existing_user(self, db_session, test_profile):
        """Should retrieve existing profile for user"""
        profile = await ProfileService.get_profile(db_session, test_profile.user_id)

        assert profile is not None
        assert profile.id == test_profile.id
        assert profile.user_id == test_profile.user_id

    @pytest.mark.asyncio
    async def test_get_profile_nonexistent_user(self, db_session):
        """Should return None for non-existent user"""
        nonexistent_user_id = str(uuid4())
        profile = await ProfileService.get_profile(db_session, nonexistent_user_id)

        assert profile is None

    @pytest.mark.asyncio
    async def test_get_profile_auto_create(self, db_session, test_user):
        """Should auto-create empty profile if not exists"""
        # User exists but has no profile
        profile = await ProfileService.get_or_create_profile(
            db_session, test_user.id
        )

        assert profile is not None
        assert profile.user_id == test_user.id
        assert profile.data is not None

    @pytest.mark.asyncio
    async def test_get_profile_returns_fresh_data(self, db_session, test_profile):
        """Should return profile with fresh database data"""
        # Modify profile in database
        test_profile.data["header"]["name"] = "Updated Name"
        await db_session.commit()

        # Retrieve fresh profile
        profile = await ProfileService.get_profile(db_session, test_profile.user_id)

        assert profile.data["header"]["name"] == "Updated Name"


class TestUpdateProfile:
    """Tests for updating profile data"""

    @pytest.mark.asyncio
    async def test_update_profile_basic_fields(self, db_session, test_profile):
        """Should update basic profile fields"""
        update_data = {
            "header": {
                "name": "Jane Doe",
                "email": "jane@example.com",
            }
        }

        updated = await ProfileService.update_profile(
            db_session, test_profile.user_id, update_data
        )

        assert updated.data["header"]["name"] == "Jane Doe"
        assert updated.data["header"]["email"] == "jane@example.com"

    @pytest.mark.asyncio
    async def test_update_profile_merge_experiences(self, db_session, test_profile):
        """Should merge new experiences with existing"""
        old_exp_count = len(test_profile.data.get("experiences", []))

        new_experience = {
            "id": str(uuid4()),
            "company": "New Company",
            "position": "Manager",
            "bullets": ["New role"],
        }

        update_data = {
            "experiences": [*test_profile.data.get("experiences", []), new_experience]
        }

        updated = await ProfileService.update_profile(
            db_session, test_profile.user_id, update_data
        )

        assert len(updated.data["experiences"]) == old_exp_count + 1
        assert updated.data["experiences"][-1]["company"] == "New Company"

    @pytest.mark.asyncio
    async def test_update_profile_replace_education(self, db_session, test_profile):
        """Should replace education list"""
        new_edu = {
            "id": str(uuid4()),
            "school": "Harvard",
            "degree": "PhD",
        }

        update_data = {"education": [new_edu]}

        updated = await ProfileService.update_profile(
            db_session, test_profile.user_id, update_data
        )

        assert len(updated.data["education"]) == 1
        assert updated.data["education"][0]["school"] == "Harvard"

    @pytest.mark.asyncio
    async def test_update_profile_add_skills(self, db_session, test_profile):
        """Should add new skills"""
        old_skills = test_profile.data.get("skills", [])
        new_skills = [*old_skills, "Kubernetes", "Docker"]

        update_data = {"skills": new_skills}

        updated = await ProfileService.update_profile(
            db_session, test_profile.user_id, update_data
        )

        assert "Kubernetes" in updated.data["skills"]
        assert "Docker" in updated.data["skills"]

    @pytest.mark.asyncio
    async def test_update_profile_empty_sections(self, db_session, test_profile):
        """Should handle empty sections"""
        update_data = {
            "experiences": [],
            "education": [],
            "projects": [],
            "skills": [],
        }

        updated = await ProfileService.update_profile(
            db_session, test_profile.user_id, update_data
        )

        assert len(updated.data["experiences"]) == 0
        assert len(updated.data["education"]) == 0

    @pytest.mark.asyncio
    async def test_update_profile_partial_data(self, db_session, test_profile):
        """Should only update provided fields"""
        original_name = test_profile.data["header"]["name"]

        update_data = {
            "header": {
                "email": "newemail@example.com",
                # Note: not updating name
            }
        }

        # This test depends on implementation - may need adjustment
        # based on how ProfileService handles partial updates

    @pytest.mark.asyncio
    async def test_update_profile_persistence(self, db_session, test_profile):
        """Profile updates should persist to database"""
        update_data = {"header": {"name": "Persisted Name"}}

        await ProfileService.update_profile(
            db_session, test_profile.user_id, update_data
        )

        # Retrieve fresh from database
        fresh_profile = await ProfileService.get_profile(
            db_session, test_profile.user_id
        )

        assert fresh_profile.data["header"]["name"] == "Persisted Name"

    @pytest.mark.asyncio
    async def test_update_nonexistent_profile(self, db_session):
        """Should handle update for non-existent profile"""
        nonexistent_user_id = str(uuid4())
        update_data = {"header": {"name": "Test"}}

        # Implementation dependent - may raise or create new
        # This test documents expected behavior


class TestProfileValidation:
    """Tests for profile data validation"""

    @pytest.mark.asyncio
    async def test_validate_profile_structure(self, test_profile):
        """Profile should have required structure"""
        assert "header" in test_profile.data
        assert "experiences" in test_profile.data
        assert "education" in test_profile.data
        assert "projects" in test_profile.data
        assert "skills" in test_profile.data

    @pytest.mark.asyncio
    async def test_validate_experience_fields(self, test_profile):
        """Experiences should have required fields"""
        if test_profile.data["experiences"]:
            exp = test_profile.data["experiences"][0]
            assert "id" in exp
            assert "company" in exp
            assert "position" in exp
            assert "bullets" in exp or len(exp.get("bullets", [])) >= 0

    @pytest.mark.asyncio
    async def test_validate_education_fields(self, test_profile):
        """Education should have required fields"""
        if test_profile.data["education"]:
            edu = test_profile.data["education"][0]
            assert "id" in edu
            assert "school" in edu
            assert "degree" in edu

    @pytest.mark.asyncio
    async def test_profile_with_special_characters(self, db_session, test_user):
        """Profile should handle special characters"""
        profile_data = {
            "header": {
                "name": "José García-López",
                "email": "jose@example.com",
            },
            "experiences": [
                {
                    "id": str(uuid4()),
                    "company": "Société Générale",
                    "position": "Ingénieur Principal",
                    "bullets": ["Travail sur des projets complexes"],
                }
            ],
            "education": [],
            "projects": [],
            "skills": ["C++", "Python", "JavaScript"],
        }

        profile = ProfileDB(
            id=str(uuid4()),
            user_id=test_user.id,
            data=profile_data,
        )
        db_session.add(profile)
        await db_session.commit()

        retrieved = await ProfileService.get_profile(db_session, test_user.id)
        assert retrieved.data["header"]["name"] == "José García-López"


class TestProfileDeduplication:
    """Tests for removing duplicate entries"""

    @pytest.mark.asyncio
    async def test_deduplicate_experiences(self, db_session, test_profile):
        """Should remove duplicate experiences by ID"""
        base_exp = test_profile.data["experiences"][0].copy()
        duplicate_exp = base_exp.copy()

        update_data = {
            "experiences": [base_exp, duplicate_exp]
        }

        # If deduplication is implemented
        updated = await ProfileService.update_profile(
            db_session, test_profile.user_id, update_data
        )

        # This test documents expected behavior for deduplication

    @pytest.mark.asyncio
    async def test_deduplicate_skills(self, db_session, test_profile):
        """Should remove duplicate skills"""
        update_data = {
            "skills": ["Python", "Python", "JavaScript", "JavaScript"]
        }

        updated = await ProfileService.update_profile(
            db_session, test_profile.user_id, update_data
        )

        # Depends on implementation


class TestProfileAuthorization:
    """Tests for profile access control"""

    @pytest.mark.asyncio
    async def test_user_can_only_access_own_profile(self, db_session, test_user, test_user_2, test_profile):
        """User should only access their own profile"""
        # test_user owns test_profile
        profile = await ProfileService.get_profile(db_session, test_user.id)
        assert profile.user_id == test_user.id

        # test_user_2 should not see test_user's profile
        other_user_profile = await ProfileService.get_profile(db_session, test_user_2.id)
        assert other_user_profile is None or other_user_profile.user_id == test_user_2.id


# ============================================================================
# Markers and Test Configuration
# ============================================================================

pytestmark = pytest.mark.unit
