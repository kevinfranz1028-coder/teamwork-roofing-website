interface Env {
  // Add your environment variables here
  // RESEND_API_KEY?: string;
  // TWILIO_ACCOUNT_SID?: string;
  // TWILIO_AUTH_TOKEN?: string;
}

export const onRequestPost: PagesFunction<Env> = async (context) => {
  try {
    const data = await context.request.json()

    // Basic validation
    if (!data.name || !data.phone) {
      return new Response(JSON.stringify({ error: 'Name and phone are required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      })
    }

    // Log the lead (in production, you would:
    // - Send email notification via Resend
    // - Send SMS via Twilio
    // - Save to database or CRM
    // - Send to Google Sheets, Airtable, etc.)
    console.log('New lead received:', data)

    // Example: Send email notification using Resend
    // if (context.env.RESEND_API_KEY) {
    //   const emailResponse = await fetch('https://api.resend.com/emails', {
    //     method: 'POST',
    //     headers: {
    //       'Content-Type': 'application/json',
    //       'Authorization': `Bearer ${context.env.RESEND_API_KEY}`
    //     },
    //     body: JSON.stringify({
    //       from: 'leads@teamworkroofing.com',
    //       to: 'your-email@example.com',
    //       subject: `New Lead: ${data.name}`,
    //       html: `
    //         <h2>New Lead from Website</h2>
    //         <p><strong>Name:</strong> ${data.name}</p>
    //         <p><strong>Phone:</strong> ${data.phone}</p>
    //         <p><strong>Email:</strong> ${data.email || 'Not provided'}</p>
    //         <p><strong>Service:</strong> ${data.service || 'Not specified'}</p>
    //         <p><strong>Notes:</strong> ${data.notes || 'None'}</p>
    //       `
    //     })
    //   })
    // }

    // Return success
    return new Response(JSON.stringify({
      success: true,
      message: 'Lead received successfully'
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Error processing lead:', error)
    return new Response(JSON.stringify({
      error: 'Internal server error'
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }
}
