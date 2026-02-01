"""
Sintezy SDK - Integração para sistemas de terceiros

Esta SDK permite integrar o sistema Sintezy em aplicações de terceiros,
oferecendo funcionalidades de transcrição médica e geração de documentos.

Exemplo de uso:
    from sintezy import SintezySDK

    sdk = SintezySDK(
        client_id='seu-client-id',
        client_secret='seu-client-secret'
    )

    # Criar consulta (autenticação é automática)
    appointment = sdk.create_appointment(
        user_email='medico@clinica.com',
        user_name='Dr. João Silva',
        layout={
            'fields': [
                {'name': 'Queixa Principal', 'content': '...', 'position': 0},
                {'name': 'História da Doença Atual', 'content': '...', 'position': 1},
            ]
        }
    )

    # Abrir portal para gravação
    print(appointment.portal_url)

    # Após finalizar, buscar documento
    doc = sdk.get_document(appointment.secure_id, 'document')
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


class SintezySDKError(Exception):
    """Exceção personalizada para erros da SDK"""
    def __init__(self, message: str, status_code: Optional[int] = None, code: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


@dataclass
class AuthToken:
    """Token de autenticação"""
    access_token: str
    expires_in: int
    token_type: str
    expires_at: datetime


@dataclass
class Appointment:
    """Dados de uma consulta"""
    secure_id: str
    status: str
    created_at: datetime
    portal_url: str
    title: Optional[str] = None


@dataclass
class Document:
    """Dados de um documento"""
    secure_id: str
    type: str
    content: Any
    created_at: datetime
    updated_at: Optional[datetime] = None


@dataclass
class DocumentListItem:
    """Item da lista de documentos"""
    type: str
    exists: bool
    created_at: Optional[datetime] = None


class SintezySDK:
    """
    SDK oficial para integração com a plataforma Sintezy.
    
    Args:
        client_id: ID do cliente OAuth
        client_secret: Secret do cliente OAuth
        base_url: URL base da API (padrão: https://api.sintezy.com)
    """
    
    DEFAULT_BASE_URL = 'https://api.sintezy.com'
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: Optional[str] = None
    ):
        if not client_id or not client_secret:
            raise SintezySDKError('client_id and client_secret are required')
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self._token: Optional[AuthToken] = None
    
    # ============================================================
    # AUTENTICAÇÃO
    # ============================================================
    
    def authenticate(self) -> AuthToken:
        """
        Autentica a aplicação usando OAuth 2.0 Client Credentials.
        
        Returns:
            Token de acesso
        """
        response = requests.post(
            f'{self.base_url}/oauth/token',
            json={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            },
            headers={'Content-Type': 'application/json'}
        )
        
        if not response.ok:
            error = response.json() if response.text else {}
            raise SintezySDKError(
                error.get('message', 'Authentication failed'),
                response.status_code,
                'AUTH_FAILED'
            )
        
        data = response.json()
        self._token = AuthToken(
            access_token=data['access_token'],
            expires_in=data['expires_in'],
            token_type=data['token_type'],
            expires_at=datetime.now() + timedelta(seconds=data['expires_in'])
        )
        
        return self._token
    
    def is_authenticated(self) -> bool:
        """Verifica se está autenticado e se o token ainda é válido"""
        if not self._token:
            return False
        # Considera expirado se faltar menos de 60 segundos
        return self._token.expires_at > datetime.now() + timedelta(seconds=60)
    
    def get_token(self) -> Optional[AuthToken]:
        """Retorna o token atual (ou None se não autenticado)"""
        return self._token
    
    def _ensure_authenticated(self) -> AuthToken:
        """Garante que há um token válido, re-autenticando se necessário"""
        if not self.is_authenticated():
            return self.authenticate()
        return self._token
    
    # ============================================================
    # APPOINTMENTS (CONSULTAS)
    # ============================================================
    
    def create_appointment(
        self,
        user_email: str,
        user_name: str,
        layout: Dict[str, Any],
        user_phone: Optional[str] = None,
        user_occupation: Optional[str] = None,
        user_occupation_doc: Optional[str] = None,
        appointment_type: str = 'NORMAL',
        modality: str = 'PRESENCIAL',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Appointment:
        """
        Cria uma nova consulta (appointment).
        
        Args:
            user_email: Email do usuário (médico/profissional)
            user_name: Nome do usuário
            layout: Layout da consulta com campos
            user_phone: Telefone do usuário (opcional)
            user_occupation: Profissão/especialidade (opcional)
            user_occupation_doc: Documento profissional (opcional)
            appointment_type: Tipo da consulta (NORMAL ou RETORNO)
            modality: Modalidade (PRESENCIAL ou ONLINE)
            metadata: Metadados extras (opcional)
        
        Returns:
            Dados da consulta criada
        """
        data = self._request('POST', '/sdk/appointments', {
            'userEmail': user_email,
            'userName': user_name,
            'layout': layout,
            'userPhone': user_phone,
            'userOccupation': user_occupation,
            'userOccupationDoc': user_occupation_doc,
            'type': appointment_type,
            'modality': modality,
            'metadata': metadata,
        })
        
        return Appointment(
            secure_id=data['secureId'],
            status=data['status'],
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')),
            portal_url=data['portalUrl'],
            title=data.get('title')
        )
    
    def get_appointment(self, appointment_id: str) -> Appointment:
        """
        Busca uma consulta pelo ID.
        
        Args:
            appointment_id: ID seguro da consulta
        
        Returns:
            Dados da consulta
        """
        data = self._request('GET', f'/sdk/appointments/{appointment_id}')
        
        return Appointment(
            secure_id=data['secureId'],
            status=data['status'],
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')),
            portal_url=data['portalUrl'],
            title=data.get('title')
        )
    
    def delete_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """
        Exclui uma consulta (soft delete).
        
        Args:
            appointment_id: ID seguro da consulta
        
        Returns:
            Confirmação da exclusão
        """
        return self._request('DELETE', f'/sdk/appointments/{appointment_id}')
    
    # ============================================================
    # DOCUMENTOS
    # ============================================================
    
    def generate_document(self, appointment_id: str, document_type: str) -> Document:
        """
        Gera um documento a partir de uma consulta.
        
        Args:
            appointment_id: ID seguro da consulta
            document_type: Tipo do documento (document, prescription, certificate, etc.)
        
        Returns:
            Documento gerado
        """
        data = self._request('POST', f'/sdk/appointments/{appointment_id}/documents', {
            'documentType': document_type
        })
        
        return Document(
            secure_id=data['secureId'],
            type=data['type'],
            content=data['content'],
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00')) if data.get('updatedAt') else None
        )
    
    def get_document(self, appointment_id: str, document_type: str) -> Document:
        """
        Busca um documento específico de uma consulta.
        
        Args:
            appointment_id: ID seguro da consulta
            document_type: Tipo do documento
        
        Returns:
            Dados do documento
        """
        data = self._request('GET', f'/sdk/appointments/{appointment_id}/documents/{document_type}')
        
        return Document(
            secure_id=data['secureId'],
            type=data['type'],
            content=data['content'],
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00')) if data.get('updatedAt') else None
        )
    
    def list_documents(self, appointment_id: str) -> List[DocumentListItem]:
        """
        Lista todos os documentos de uma consulta.
        
        Args:
            appointment_id: ID seguro da consulta
        
        Returns:
            Lista com status de cada tipo de documento
        """
        data = self._request('GET', f'/sdk/appointments/{appointment_id}/documents')
        
        return [
            DocumentListItem(
                type=item['type'],
                exists=item['exists'],
                created_at=datetime.fromisoformat(item['createdAt'].replace('Z', '+00:00')) if item.get('createdAt') else None
            )
            for item in data
        ]
    
    # ============================================================
    # HELPERS INTERNOS
    # ============================================================
    
    def _request(self, method: str, path: str, body: Optional[Dict] = None) -> Any:
        """Faz uma requisição autenticada para a API"""
        self._ensure_authenticated()
        
        response = requests.request(
            method,
            f'{self.base_url}{path}',
            json=body,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self._token.access_token}'
            }
        )
        
        if not response.ok:
            error = response.json() if response.text else {}
            raise SintezySDKError(
                error.get('message', f'Request failed: {method} {path}'),
                response.status_code,
                error.get('code')
            )
        
        return response.json()


# Exports
__all__ = [
    'SintezySDK',
    'SintezySDKError',
    'AuthToken',
    'Appointment',
    'Document',
    'DocumentListItem',
]
__version__ = '0.1.0'
