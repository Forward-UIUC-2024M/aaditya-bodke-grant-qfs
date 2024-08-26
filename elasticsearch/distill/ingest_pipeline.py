def get_ingest_pipeline(inference_id):
  return  {
    "description": "Pipeline to create separate embeddings for multiple fields, average them, and normalize the result",
    "processors": [
      {
        "script": {
          "lang": "painless",
          "source": """
            def formatField(def field, def maxLen) {
              if (field == null) {
                return " ";
              }
              if (field instanceof List) {
                field = field.join(",");
              }
              
              field = field.toString();

              if (maxLen > 0) {
              field = field.substring(0, maxLen);
              }
              
              return field;
            }
            
            ctx.truncated_description = formatField(ctx.description, ctx.description_truncate_length);
            ctx.truncated_submission_info = formatField(ctx.submission_info, ctx.submission_info_truncate_length);
            ctx.truncated_eligibility = formatField(ctx.eligibility, ctx.eligibility_truncate_length);
            
            ctx.text_all_titles = formatField(ctx.all_titles, 0);
            ctx.text_user_categories = formatField(ctx.user_categories, 0);
            ctx.text_all_applicant_types = formatField(ctx.all_applicant_types, 0);
          """
        }
      },
      {
        "inference": {
          "model_id": inference_id,
          "input_output": {
            "input_field": "truncated_description",
            "output_field": "embedding_description"
          }
        }
      },
      {
        "inference": {
          "model_id": inference_id,
          "input_output": {
            "input_field": "truncated_submission_info",
            "output_field": "embedding_submission_info"
          }
        }
      },
      {
        "inference": {
          "model_id": inference_id,
          "input_output": {
            "input_field": "truncated_eligibility",
            "output_field": "embedding_eligibility"
          }
        }
      },
      {
        "inference": {
          "model_id": inference_id,
          "input_output": {
            "input_field": "text_all_titles",
            "output_field": "embedding_all_titles"
          }
        }
      },
      {
        "inference": {
          "model_id": inference_id,
          "input_output": {
            "input_field": "text_user_categories",
            "output_field": "embedding_user_categories"
          }
        }
      },
      {
        "inference": {
          "model_id": inference_id,
          "input_output": {
            "input_field": "text_all_applicant_types",
            "output_field": "embedding_all_applicant_types"
          }
        }
      },
      {
        "script": {
          "lang": "painless",
          "source": """
            // Collect all embeddings
            def embeddings = [];
            if (ctx.containsKey('embedding_description')) embeddings.add(ctx.embedding_description);
            if (ctx.containsKey('embedding_submission_info')) embeddings.add(ctx.embedding_submission_info);
            if (ctx.containsKey('embedding_eligibility')) embeddings.add(ctx.embedding_eligibility);
            if (ctx.containsKey('embedding_all_titles')) embeddings.add(ctx.embedding_all_titles);  
            if (ctx.containsKey('embedding_user_categories')) embeddings.add(ctx.embedding_user_categories);
            if (ctx.containsKey('embedding_all_applicant_types')) embeddings.add(ctx.embedding_all_applicant_types);
            
            if (embeddings.size() > 0) {
              // Calculate the average embedding
              def avgEmbedding = new double[embeddings[0].length];
              for (int i = 0; i < avgEmbedding.length; i++) {
                double sum = 0;
                for (def embedding : embeddings) {
                  sum += embedding[i];
                }
                avgEmbedding[i] = sum / embeddings.size();
              }
              
              // Normalize the average embedding to unit length
              double sumOfSquares = 0;
              for (double val : avgEmbedding) {
                sumOfSquares += val * val;
              }
              double magnitude = Math.sqrt(sumOfSquares);
              
              def normalizedEmbedding = new double[avgEmbedding.length];
              for (int i = 0; i < avgEmbedding.length; i++) {
                normalizedEmbedding[i] = avgEmbedding[i] / magnitude;
              }
              
              // Set the final normalized embedding
              ctx.embeddings = normalizedEmbedding;
            }
          """
        }
      },
      {
        "remove": {
          "field": [
            "text_all_titles",
            "truncated_submission_info",
            "truncated_description",
            "truncated_eligibility",
            "text_user_categories",
            "text_all_applicant_types",
            "embedding_all_titles",
            "embedding_submission_info",
            "embedding_description",
            "embedding_eligibility",
            "embedding_user_categories",
            "embedding_all_applicant_types"
          ]
        }
      }
    ],
    "on_failure": [
      {
        "set": {
          "field": "error_message",
          "value": "Failed to process document: {{_ingest.on_failure_message}}"
        }
      }
    ]
  }
