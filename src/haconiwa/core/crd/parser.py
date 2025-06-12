"""
CRD Parser for Haconiwa v1.0
"""

import yaml
from pathlib import Path
from typing import Union, List, Dict, Any
from pydantic import ValidationError

from .models import (
    SpaceCRD, AgentCRD, TaskCRD, PathScanCRD, DatabaseCRD, CommandPolicyCRD, OrganizationCRD
)


class CRDValidationError(Exception):
    """CRD validation error"""
    pass


class CRDParser:
    """CRD Parser for YAML to CRD objects"""
    
    def __init__(self):
        self.crd_classes = {
            "Space": SpaceCRD,
            "Agent": AgentCRD,
            "Task": TaskCRD,
            "PathScan": PathScanCRD,
            "Database": DatabaseCRD,
            "CommandPolicy": CommandPolicyCRD,
            "Organization": OrganizationCRD
        }
        self.supported_api_versions = ["haconiwa.dev/v1"]
    
    def parse_yaml(self, yaml_content: str) -> Union[SpaceCRD, AgentCRD, TaskCRD, PathScanCRD, DatabaseCRD, CommandPolicyCRD, OrganizationCRD]:
        """Parse single YAML document to CRD object"""
        try:
            data = yaml.safe_load(yaml_content)
            return self._parse_crd_data(data)
        except yaml.YAMLError as e:
            raise CRDValidationError(f"Invalid YAML: {e}")
        except ValidationError as e:
            raise CRDValidationError(f"Validation error: {e}")
    
    def parse_multi_yaml(self, yaml_content: str) -> List[Union[SpaceCRD, AgentCRD, TaskCRD, PathScanCRD, DatabaseCRD, CommandPolicyCRD, OrganizationCRD]]:
        """Parse multi-document YAML to list of CRD objects"""
        try:
            documents = yaml.safe_load_all(yaml_content)
            crds = []
            for data in documents:
                if data:  # Skip empty documents
                    crds.append(self._parse_crd_data(data))
            return crds
        except yaml.YAMLError as e:
            raise CRDValidationError(f"Invalid YAML: {e}")
        except ValidationError as e:
            raise CRDValidationError(f"Validation error: {e}")
    
    def parse_file(self, file_path: Path) -> Union[SpaceCRD, AgentCRD, TaskCRD, PathScanCRD, DatabaseCRD, CommandPolicyCRD, OrganizationCRD]:
        """Parse YAML file to CRD object"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_yaml(content)
        except FileNotFoundError:
            raise CRDValidationError(f"File not found: {file_path}")
        except Exception as e:
            raise CRDValidationError(f"Error reading file {file_path}: {e}")
    
    def parse_multi_file(self, file_path: Path) -> List[Union[SpaceCRD, AgentCRD, TaskCRD, PathScanCRD, DatabaseCRD, CommandPolicyCRD, OrganizationCRD]]:
        """Parse multi-document YAML file to list of CRD objects"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_multi_yaml(content)
        except FileNotFoundError:
            raise CRDValidationError(f"File not found: {file_path}")
        except Exception as e:
            raise CRDValidationError(f"Error reading file {file_path}: {e}")
    
    def _parse_crd_data(self, data: Dict[str, Any]) -> Union[SpaceCRD, AgentCRD, TaskCRD, PathScanCRD, DatabaseCRD, CommandPolicyCRD, OrganizationCRD]:
        """Parse CRD data dictionary to CRD object"""
        # Validate required fields
        if not isinstance(data, dict):
            raise CRDValidationError("CRD must be a dictionary")
        
        if "apiVersion" not in data:
            raise CRDValidationError("apiVersion is required")
        
        if "kind" not in data:
            raise CRDValidationError("kind is required")
        
        if "metadata" not in data:
            raise CRDValidationError("metadata is required")
        
        if "spec" not in data:
            raise CRDValidationError("spec is required")
        
        # Validate API version
        api_version = data["apiVersion"]
        if api_version not in self.supported_api_versions:
            raise CRDValidationError(f"Unsupported apiVersion: {api_version}")
        
        # Validate kind
        kind = data["kind"]
        if kind not in self.crd_classes:
            raise CRDValidationError(f"Unsupported kind: {kind}")
        
        # Get appropriate CRD class
        crd_class = self.crd_classes[kind]
        
        try:
            # Create CRD object with validation
            return crd_class(**data)
        except ValidationError as e:
            raise CRDValidationError(f"CRD validation failed for {kind}: {e}")
    
    def validate_crd(self, crd: Union[SpaceCRD, AgentCRD, TaskCRD, PathScanCRD, DatabaseCRD, CommandPolicyCRD]) -> bool:
        """Validate CRD object"""
        try:
            # Additional validation logic if needed
            if isinstance(crd, SpaceCRD):
                return self._validate_space_crd(crd)
            elif isinstance(crd, AgentCRD):
                return self._validate_agent_crd(crd)
            elif isinstance(crd, TaskCRD):
                return self._validate_task_crd(crd)
            elif isinstance(crd, PathScanCRD):
                return self._validate_pathscan_crd(crd)
            elif isinstance(crd, DatabaseCRD):
                return self._validate_database_crd(crd)
            elif isinstance(crd, CommandPolicyCRD):
                return self._validate_commandpolicy_crd(crd)
            return True
        except Exception as e:
            raise CRDValidationError(f"CRD validation failed: {e}")
    
    def _validate_space_crd(self, crd: SpaceCRD) -> bool:
        """Validate Space CRD"""
        if not crd.spec.nations:
            raise CRDValidationError("nations cannot be empty")
        
        for nation in crd.spec.nations:
            if not nation.cities:
                raise CRDValidationError(f"Nation {nation.id} must have at least one city")
            
            for city in nation.cities:
                if not city.villages:
                    raise CRDValidationError(f"City {city.id} must have at least one village")
                
                for village in city.villages:
                    if not village.companies:
                        raise CRDValidationError(f"Village {village.id} must have at least one company")
        
        return True
    
    def _validate_agent_crd(self, crd: AgentCRD) -> bool:
        """Validate Agent CRD"""
        # Role validation is already done in model
        return True
    
    def _validate_task_crd(self, crd: TaskCRD) -> bool:
        """Validate Task CRD"""
        # Branch validation is already done in model
        return True
    
    def _validate_pathscan_crd(self, crd: PathScanCRD) -> bool:
        """Validate PathScan CRD"""
        if not crd.spec.include:
            raise CRDValidationError("PathScan must have at least one include pattern")
        return True
    
    def _validate_database_crd(self, crd: DatabaseCRD) -> bool:
        """Validate Database CRD"""
        if not crd.spec.dsn:
            raise CRDValidationError("Database DSN cannot be empty")
        return True
    
    def _validate_commandpolicy_crd(self, crd: CommandPolicyCRD) -> bool:
        """Validate CommandPolicy CRD"""
        if not crd.spec.global_commands and not crd.spec.roles:
            raise CRDValidationError("CommandPolicy must have either global commands or role-specific policies")
        return True 