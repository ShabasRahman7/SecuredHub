"""
Tests for standards models.

Tests:
- ComplianceStandard properties and methods
- ComplianceRule validation
- RepositoryStandard assignments
"""
import pytest
from django.core.exceptions import ValidationError
from standards.models import ComplianceStandard, ComplianceRule, RepositoryStandard


# ============================================
# ComplianceStandard Tests
# ============================================

@pytest.mark.django_db
class TestComplianceStandard:
    """Tests for the ComplianceStandard model."""
    
    def test_create_builtin_standard(self):
        """Test creating a built-in standard."""
        standard = ComplianceStandard.objects.create(
            name="Test Standard",
            slug="test-standard",
            description="A test standard",
            version="1.0",
            is_builtin=True,
            is_active=True
        )
        
        assert standard.id is not None
        assert standard.name == "Test Standard"
        assert standard.is_builtin is True
        assert standard.organization is None
    
    def test_create_custom_standard(self, tenant):
        """Test creating a custom standard for an organization."""
        standard = ComplianceStandard.objects.create(
            name="Custom Standard",
            slug="custom-standard",
            description="A custom standard",
            version="1.0",
            is_builtin=False,
            organization=tenant,
            is_active=True
        )
        
        assert standard.id is not None
        assert standard.is_builtin is False
        assert standard.organization == tenant
    
    def test_standard_str(self, builtin_standard):
        """Test __str__ method."""
        assert "Test Standard" in str(builtin_standard)
        assert "1.0" in str(builtin_standard)
    
    def test_total_weight_no_rules(self, builtin_standard):
        """Test total_weight returns 0 when no rules exist."""
        assert builtin_standard.total_weight == 0
    
    def test_total_weight_with_rules(self, standard_with_rules):
        """Test total_weight sums all active rule weights."""
        # standard_with_rules has rules with weights 5, 3, 8 = 16
        assert standard_with_rules.total_weight == 16
    
    def test_total_weight_excludes_inactive(self, standard_with_rules):
        """Test total_weight excludes inactive rules."""
        # Deactivate one rule
        rule = standard_with_rules.rules.first()
        rule.is_active = False
        rule.save()
        
        # total_weight should decrease
        original_weight = rule.weight
        assert standard_with_rules.total_weight == 16 - original_weight
    
    def test_rule_count_no_rules(self, builtin_standard):
        """Test rule_count returns 0 when no rules exist."""
        assert builtin_standard.rule_count == 0
    
    def test_rule_count_with_rules(self, standard_with_rules):
        """Test rule_count counts active rules."""
        assert standard_with_rules.rule_count == 3
    
    def test_rule_count_excludes_inactive(self, standard_with_rules):
        """Test rule_count excludes inactive rules."""
        # Deactivate one rule
        rule = standard_with_rules.rules.first()
        rule.is_active = False
        rule.save()
        
        assert standard_with_rules.rule_count == 2


# ============================================
# ComplianceRule Tests
# ============================================

@pytest.mark.django_db
class TestComplianceRule:
    """Tests for the ComplianceRule model."""
    
    def test_create_rule(self, builtin_standard):
        """Test creating a compliance rule."""
        rule = ComplianceRule.objects.create(
            standard=builtin_standard,
            name="Test Rule",
            description="A test rule",
            rule_type="file_exists",
            check_config={"path": "README.md"},
            weight=5,
            severity="medium",
            is_active=True
        )
        
        assert rule.id is not None
        assert rule.standard == builtin_standard
        assert rule.check_config['path'] == "README.md"
    
    def test_rule_str(self, compliance_rule):
        """Test __str__ method."""
        assert "README Check" in str(compliance_rule)
        assert "Test Standard" in str(compliance_rule)
    
    def test_rule_weight_validation_min(self, builtin_standard):
        """Test weight has minimum value validation."""
        # Weight of 0 should fail validator (min is 1)
        rule = ComplianceRule(
            standard=builtin_standard,
            name="Bad Weight",
            rule_type="file_exists",
            check_config={},
            weight=0
        )
        
        with pytest.raises(ValidationError):
            rule.full_clean()
    
    def test_rule_weight_validation_max(self, builtin_standard):
        """Test weight has maximum value validation."""
        # Weight of 11 should fail validator (max is 10)
        rule = ComplianceRule(
            standard=builtin_standard,
            name="Bad Weight",
            rule_type="file_exists",
            check_config={},
            weight=11
        )
        
        with pytest.raises(ValidationError):
            rule.full_clean()
    
    def test_rule_types(self, builtin_standard):
        """Test all rule types can be created."""
        rule_types = ['file_exists', 'file_forbidden', 'folder_exists', 'config_check', 'pattern_match', 'hygiene']
        
        for i, rt in enumerate(rule_types):
            rule = ComplianceRule.objects.create(
                standard=builtin_standard,
                name=f"Rule {i}",
                rule_type=rt,
                check_config={},
                weight=5
            )
            assert rule.rule_type == rt
    
    def test_rule_ordering(self, standard_with_rules):
        """Test rules are ordered by standard, order, name."""
        rules = list(standard_with_rules.rules.all())
        
        # Should be ordered by 'order' field
        orders = [r.order for r in rules]
        assert orders == sorted(orders)


# ============================================
# RepositoryStandard Tests
# ============================================

@pytest.mark.django_db
class TestRepositoryStandard:
    """Tests for the RepositoryStandard model."""
    
    def test_assign_standard_to_repository(self, repository, builtin_standard, admin_user):
        """Test assigning a standard to a repository."""
        assignment = RepositoryStandard.objects.create(
            repository=repository,
            standard=builtin_standard,
            assigned_by=admin_user,
            is_active=True
        )
        
        assert assignment.id is not None
        assert assignment.repository == repository
        assert assignment.standard == builtin_standard
    
    def test_assignment_str(self, repository_with_standard, builtin_standard):
        """Test __str__ method for assignment."""
        assignment = RepositoryStandard.objects.get(
            repository=repository_with_standard,
            standard=builtin_standard
        )
        
        assert "test-repo" in str(assignment)
        assert "Test Standard" in str(assignment)
    
    def test_unique_together_constraint(self, repository, builtin_standard, admin_user):
        """Test each repository-standard pair is unique."""
        RepositoryStandard.objects.create(
            repository=repository,
            standard=builtin_standard,
            assigned_by=admin_user
        )
        
        # Creating duplicate should fail
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            RepositoryStandard.objects.create(
                repository=repository,
                standard=builtin_standard,
                assigned_by=admin_user
            )
