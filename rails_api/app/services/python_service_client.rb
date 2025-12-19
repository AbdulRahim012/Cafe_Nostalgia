class PythonServiceClient
  include HTTParty
  
  base_uri ENV.fetch('PYTHON_SERVICE_URL', 'http://localhost:8000')
  
  def ask_question(store_id:, question:)
    response = self.class.post('/api/v1/analyze', {
      body: {
        store_id: store_id,
        question: question
      }.to_json,
      headers: {
        'Content-Type' => 'application/json'
      },
      timeout: 30
    })
    
    if response.success?
      parsed_response = response.parsed_response
      {
        success: true,
        answer: parsed_response['answer'],
        confidence: parsed_response['confidence'],
        query_used: parsed_response['query_used'],
        data: parsed_response['data']
      }
    else
      parsed_response = response.parsed_response rescue {}
      {
        success: false,
        error: parsed_response['detail'] || parsed_response['error'] || 'Python service error'
      }
    end
  rescue => e
    {
      success: false,
      error: "Connection error: #{e.message}"
    }
  end
end

