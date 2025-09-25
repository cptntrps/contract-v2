"""
Refactored analyze_contract route handler - HTTP concerns only.
Following architectural standards: delegates to use case, no business logic.
"""

@analysis_bp.route('/analyze-contract', methods=['POST'])
def analyze_contract():
    """
    HTTP endpoint for contract analysis initiation.
    
    Purpose: Handles HTTP request/response for contract analysis workflow.
    Delegates all business logic to AnalyzeContractUseCase following clean architecture.
    
    Request Body:
        {
            "contract_id": "string",               // Required: Contract identifier
            "analysis_options": {                  // Optional: Analysis configuration
                "llm_settings": {...},
                "analysis_settings": {...},
                "nlp_settings": {...}
            }
        }
    
    Returns:
        JSON response with analysis results or error information
    
    Raises:
        400: Invalid request format or missing required parameters
        404: Contract not found
        422: Business logic validation failure
        500: Internal server error
    
    AI Context: This is a thin HTTP adapter that handles only request/response concerns.
    All business logic is in AnalyzeContractUseCase. For debugging analysis issues,
    check the use case implementation, not this route handler.
    """
    try:
        # Parse and validate HTTP request
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                'success': False,
                'error': 'No request data provided'
            }), 400
        
        contract_id = request_data.get('contract_id')
        if not contract_id:
            return jsonify({
                'success': False,
                'error': 'Contract ID is required'
            }), 400
        
        analysis_options = request_data.get('analysis_options', {})
        
        logger.debug(f"Analysis request received for contract: {contract_id}")
        
        # Create analysis request object
        analysis_request = AnalysisRequest(
            contract_id=contract_id,
            analysis_options=analysis_options,
            user_context={'ip_address': request.remote_addr}
        )
        
        # Delegate to application use case
        use_case = AnalyzeContractUseCase()
        analysis_result = use_case.execute(analysis_request)
        
        # Format HTTP response
        response_data = {
            'success': True,
            'analysis_id': analysis_result.analysis_id,
            'result': analysis_result.to_dict(),
            'message': 'Contract analysis completed successfully'
        }
        
        logger.info(f"Analysis completed successfully: {analysis_result.analysis_id}")
        return jsonify(response_data), 200
        
    except ValidationError as e:
        logger.warning(f"Validation error in analyze_contract: {e}")
        return jsonify({
            'success': False,
            'error': 'Request validation failed',
            'details': str(e)
        }), 400
    except NotFoundError as e:
        logger.warning(f"Not found error in analyze_contract: {e}")
        return jsonify({
            'success': False,
            'error': f'{e.resource_type.title()} not found',
            'resource_id': e.resource_id
        }), 404
    except (TemplateMatchingError, AnalysisError) as e:
        logger.error(f"Business logic error in analyze_contract: {e}")
        return jsonify({
            'success': False,
            'error': 'Analysis failed',
            'details': str(e)
        }), 422
    except Exception as e:
        logger.error(f"Unexpected error in analyze_contract: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred during analysis'
        }), 500