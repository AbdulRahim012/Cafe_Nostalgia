module Api
  module V1
    class QuestionsController < ApplicationController
      before_action :validate_request

      def create
        question = params[:question]
        store_id = params[:store_id]

        # Forward request to Python AI service
        response = PythonServiceClient.new.ask_question(
          store_id: store_id,
          question: question
        )

        if response[:success]
          render json: {
            answer: response[:answer],
            confidence: response[:confidence] || 'medium',
            query_used: response[:query_used],
            data: response[:data]
          }, status: :ok
        else
          render json: {
            error: response[:error] || 'Failed to process question'
          }, status: :unprocessable_entity
        end
      rescue => e
        Rails.logger.error "Error processing question: #{e.message}"
        render json: {
          error: 'An error occurred while processing your question',
          details: e.message
        }, status: :internal_server_error
      end

      private

      def validate_request
        unless params[:question].present?
          render json: { error: 'Question parameter is required' }, status: :bad_request
          return
        end

        unless params[:store_id].present?
          render json: { error: 'store_id parameter is required' }, status: :bad_request
          return
        end
      end
    end
  end
end

