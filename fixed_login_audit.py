@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Enhanced debug logging
        print(f"Login attempt for username: {username}, password: {password[:2]}***")
        logger.info(f"Login attempt for username: {username}")
        
        # Get the user first
        user = User.query.filter_by(username=username).first()
        
        if user:
            # Log user details for debugging
            print(f"User found: ID={user.id}, Username={user.username}, Role={user.role}, Active={user.is_active}")
            logger.info(f"User found: {user.username}, role: {user.role}, active: {user.is_active}")
            
            # Check password and ensure user is active
            if user.check_password(password) and user.is_active:
                # Print the actual and expected password hashes for debugging
                print(f"Password valid for {username}. Logging in.")
                login_user(user)
                logger.info(f"User {username} successfully logged in")
                
                # Create audit log
                try:
                    audit = SecurityAudit(
                        user_id=user.id,
                        action='login',
                        action_details='User logged in successfully',
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string
                    )
                    db.session.add(audit)
                    db.session.commit()
                except Exception as e:
                    logger.error(f"Error creating login audit: {str(e)}")
                    db.session.rollback()
                
                return redirect(url_for('dashboard')) 