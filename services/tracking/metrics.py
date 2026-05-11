import streamlit as st
from services.config.workout_config import METRICS_FIELDS
import time
from services.persistence.exercise_repository import add_exercise
def sync_metrics_update(context):
    if not context or not hasattr(context,"state") or not context.state.playing:
        return 
    
    processor = getattr(context,"video_processor",None)

    if not processor:
        return 
    
    exercise = st.session_state.get("exercise_type")

    if not exercise:
        return 
    
    processor.set_exercise(exercise)
    latest_metrics = processor.get_latest_metrics()

    if not latest_metrics:
        return 
    if st.session_state.get("workout_completed"):
        return
    
    reps= latest_metrics.get("reps")

    st.session_state.reps = reps

    fields = METRICS_FIELDS.get(exercise)
    if not fields:
        return 
    
    for key, defaults in fields.items():
        st.session_state[key] = latest_metrics.get(key,defaults)
    
    
    reps = latest_metrics.get("reps", 0)

    reps_per_set = st.session_state.get("target_reps", 0)
    target_sets = st.session_state.get("target_sets", 0)

    max_reps = reps_per_set * target_sets

    if max_reps > 0:
        capped_reps = min(reps, max_reps)
    else:
        capped_reps = reps

    sets_completed = 0
    current_set_reps = 0
    workout_completed = False

    if reps_per_set > 0 and target_sets > 0:

        sets_completed = min(capped_reps // reps_per_set, target_sets)

        current_set_reps = capped_reps % reps_per_set

        if sets_completed >= target_sets:
            workout_completed = True
            current_set_reps = reps_per_set

    st.session_state.reps = capped_reps

    st.session_state.sets_completed = sets_completed
    st.session_state.current_set_reps = current_set_reps
    st.session_state.workout_completed = workout_completed 


    last_saved_sets = st.session_state.get("last_saved_sets_completed",0)  

    if sets_completed >0  and reps_per_set > 0 and  sets_completed >  last_saved_sets :
        newly_completed = sets_completed - last_saved_sets
        new_ts = time.time()
        started_at = st.session_state.get("set_cycle_started_at",new_ts)
        time_taken  = new_ts - started_at
        user_id = st.session_state.get("user_id",0)

        add_exercise(user_id,exercise,newly_completed*reps_per_set,newly_completed,time_taken)

        if st.session_state.get("voice_pipeline"):
            result = st.session_state.voice_pipeline.process_event(
                event = "sets_completed",
                exercise=exercise,
                metrics = latest_metrics
            )
            if result:
                st.session_state.audio_to_play , st.session_state.coach_feedback = result

        st.session_state.set_cycle_started_at = new_ts
        st.session_state.last_saved_sets_completed = sets_completed

    if workout_completed and not st.session_state.get("last_notified_workout_completed",False):
        st.session_state.last_notified_workout_completed = True
        if st.session_state.get("voice_pipeline"):
            result = st.session_state.voice_pipeline.process_event(
                event = "workout_completed",
                exercise=exercise,
                metrics = latest_metrics
            )
            if result:
                st.session_state.audio_to_play , st.session_state.coach_feedback = result

    pose_detected = latest_metrics.get("pose_detected",True)

    if not pose_detected and st.session_state.get("voice_pipeline"):
        result = st.session_state.voice_pipeline.process_event(
            event = "no_pose_detected",
            exercise=exercise,
            metrics = {"issue":"No pose detected! please step into the camera frame"}
        )
        if result:
            st.session_state.audio_to_play , st.session_state.coach_feedback = result

    last_form_feedback = st.session_state.get("last_form_feedback_at", 0)

    if time.time() - last_form_feedback > 8:

        if st.session_state.get("voice_pipeline"):

            result = st.session_state.voice_pipeline.process_event(
                event="ongoing_form_check",
                exercise=exercise,
                metrics=latest_metrics
            )

            if result:

                st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.session_state.last_form_feedback_at = time.time()
        